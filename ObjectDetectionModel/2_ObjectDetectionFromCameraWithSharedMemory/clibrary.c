#include <sys/types.h>
#include <stdlib.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>

#include <time.h>
#include <stdbool.h> 
#include <unistd.h> 

#define SHMKEY 4711
#define PIPMODE 0600

int gFd_FIFO;
int gShmId;
char pathToFIFO[] = "FIFO";

typedef struct {
	bool logosDetected;
    int logos[4];
    long timestampMemoryInsertion_Sec;
    long timestampMemoryInsertion_Nsec;
    } gLogoDetectionDataset;

gLogoDetectionDataset *gLogoDetection;

long getTimestamp_Sec(void)
{
	struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec;
}

long getTimestamp_Nsec(void)
{
	struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_nsec;
}

int initializeFIFOAndSharedMemory()
{
    int errorFlag = -1;
    
    /*Opening the read or write end of a FIFO blocks until the
    other end is also opened (by another process or thread).*/
    if ((gFd_FIFO = open(pathToFIFO, O_WRONLY, 0)) < 0)
    {
        perror("Error opening FIFO\n");
    }
    else
    {
        if ((gShmId = shmget(SHMKEY, sizeof (gLogoDetectionDataset), 0)) < 0)
        {
            perror("Error requesting SHM\n");
        }
        else
        {
            if ((gLogoDetection = (gLogoDetectionDataset*) shmat(gShmId, NULL, 0)) < (gLogoDetectionDataset*) NULL)
            {
                perror("Error attaching SHM\n");
            }
            else
            {
                errorFlag = 0;
            }
        }
    }

    return errorFlag;
}

void writeLogoDetectionDatasetToSharedMemory(gLogoDetectionDataset _logoDetection)
{
    gLogoDetection->logosDetected = _logoDetection.logosDetected;
        
    for (int i = 0; i < 4; i++)
    {
        gLogoDetection->logos[i] = _logoDetection.logos[i];
    }
        
    gLogoDetection->timestampMemoryInsertion_Sec = _logoDetection.timestampMemoryInsertion_Sec;
    gLogoDetection->timestampMemoryInsertion_Nsec = _logoDetection.timestampMemoryInsertion_Nsec;

    //Write to FIFO to announce data
    if (write(gFd_FIFO, "D", sizeof("D")) == -1)
    {
        perror("Error writing to pipe to announce new data\n");
    }
}

void detachSharedMemoryAndClosePipe()
{
    if (shmdt(gLogoDetection) == -1)
    {
        perror("Error detaching SHM\n");
    }

    // Write end-signal into the pipe
    if (write(gFd_FIFO, "E", sizeof("E")) == -1)
    {
        perror("Error writing end-signal to pipe\n");
    }

    if (close(gFd_FIFO) == -1)
    {
        perror("Error closing FIFO\n");
    }
}

/*
void resetLogoDetectionDatasetSharedMemory()
{
    if (logoDetection != NULL)
    {
        logoDetection->logosDetected = false; 

        for (int i = 0; i < 4; i++)
        {
            logoDetection->logos[i] = 0;
        }

        logoDetection->timestampMemoryInsertion_Sec = 0;
        logoDetection->timestampMemoryInsertion_Nsec = 0;
    }
}
*/