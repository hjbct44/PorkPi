/* 
 gurov was here, use this code, or don't, whatever, I don't care. If you see a giant bug with a billion legs, please let me know so it can be squashed
gcc -o hx711wp hx711wp.c -lwiringPi

HJBCT44 -some cleanup, comments, unused variables etc.  Changed to wiringpi and init type to gpio
*/

#include <stdint.h>
#include <sys/types.h>


#include <stdio.h>
#include <sched.h>
#include <string.h>
#include <stdlib.h>
#include <wiringPi.h>



#define N_SAMPLES	64
#define SPREAD		10
#define DELAY 10

#define SCK_ON  (GPIO_SET0 = (1 << CLOCK_PIN))
#define SCK_OFF (GPIO_CLR0 = (1 << CLOCK_PIN))
#define DT_R    (GPIO_IN0  & (1 << DATA_PIN))

void           reset_converter(void);
unsigned long  read_HX711_data();
void           set_gain(int r);
void           setHighPri (void);

int clock_pin;
int data_pin;


void setHighPri (void)
{
 if(piHiPri (99)==-1)
    printf ("Warning: Unable to set high priority\n") ;
}

static uint8_t sizecvt(const int read)
{
    /* digitalRead() and friends from wiringpi are defined as returning a value
       < 256. However, they are returned as int() types. This is a safety function */

    if (read > 255 || read < 0)
    {
        printf("Invalid data from wiringPi library\n");
        exit(EXIT_FAILURE);
    }
    return (uint8_t)read;
}


void power_down_hx711()
{
    digitalWrite(clock_pin, HIGH);
}

void setup_gpio()
{
    pinMode(clock_pin, OUTPUT);
    pinMode(data_pin, INPUT);
    digitalWrite(clock_pin, LOW);
}


int main(int argc, char **argv)
{
    
    
    int iErr = 0;
    
  


  int i, j;
  long tmp=0;
  long tmp_avg=0;
  long tmp_avg2;
  long offset=0;
  long two_point_five_kilo=0;
  float filter_low, filter_high;
  float spread_percent = SPREAD / 100.0 /2.0;
 
  int nsamples=N_SAMPLES;
  long samples[nsamples];
  

  if (argc <= 2) {
   printf(" Usage:  %s clock_pin data_pin [offset] [two_point_five_kilo]\n", argv[0]);
   exit(255);
  }
  
  if (argc == 3){
   clock_pin = atol(argv[1]);
   data_pin = atol(argv[2]);
  }
  
  
  if (argc ==4){
   clock_pin = atol(argv[1]);
   data_pin = atol(argv[2]);
   offset = atol(argv[3]);
  }
  
  if (argc ==5){
   clock_pin = atol(argv[1]);
   data_pin = atol(argv[2]);
   offset = atol(argv[3]);
   two_point_five_kilo = atol(argv[4]);
  }


        iErr = wiringPiSetupGpio ();
    if (iErr == -1)
        {                
        printf ("ERROR : Failed to init WiringPi %d\n", iErr);
        exit(255);
        }

  setHighPri();
  setup_gpio();
  set_gain(2);

  


  j=0;

  
  for(i=0;i<nsamples;i++) {
  	samples[i] = read_HX711_data();
  	tmp_avg += samples[i];
	delayMicroseconds(100);

  }

  tmp_avg = tmp_avg / nsamples;

  tmp_avg2 = 0;
  j=0;

  filter_low =  (float) tmp_avg * (1.0 - spread_percent);
  filter_high = (float) tmp_avg * (1.0 + spread_percent);


  for(i=0;i<nsamples;i++) {
	if ((samples[i] < filter_high && samples[i] > filter_low) || 
            (samples[i] > filter_high && samples[i] < filter_low) ) {
		tmp_avg2 += samples[i];
	        j++;
	}
  }

  if (j == 0) {
    // No Data To Consider
    printf("-1");
    exit(255);

  }

if (argc == 3){
   printf("%d\n", (tmp_avg2 / j));

  }
  
  
  if (argc == 4){
   printf("%d\n", (tmp_avg2 / j) - offset);

  }
  
   if (argc == 5){
	   
   printf("%d\n", ((tmp_avg2 / j) - offset) / ((two_point_five_kilo/2500)));

  }
  
  
	power_down_hx711();

}


void reset_converter(void) {
          digitalWrite(clock_pin, HIGH);
          delayMicroseconds(40);
          digitalWrite(clock_pin, LOW);
          delayMicroseconds(60);
}

void set_gain(int r) {
	int i;

// r = 0 - 128 gain ch a
// r = 1 - 32  gain ch b
// r = 2 - 64  gain ch a

        while( sizecvt(digitalRead(data_pin)) );

	for (i=0;i<24+r;i++) {
          digitalWrite(clock_pin, HIGH);
          delayMicroseconds(DELAY);
          digitalWrite(clock_pin, LOW);
          delayMicroseconds(DELAY);
	}
}


unsigned long read_HX711_data() {
	long reading;
	int i;


  reading = 0;


  while( sizecvt(digitalRead(data_pin)) );
        digitalWrite(clock_pin, LOW);
        delayMicroseconds(DELAY);

  for(i=0;i<24	; i++) {
        digitalWrite(clock_pin, HIGH);
		
        delayMicroseconds(DELAY);
		
        reading = reading << 1;
		
        if ( sizecvt(digitalRead(data_pin)) > 0 )  { reading++; }
		
        digitalWrite(clock_pin, LOW);
        delayMicroseconds(DELAY);
        }

        digitalWrite(clock_pin, HIGH);
        delayMicroseconds(DELAY);
        digitalWrite(clock_pin, LOW);
        delayMicroseconds(DELAY);


 if (reading & 0x800000) {
	reading |= (long) ~0xffffff;
 }




  return (reading);

}


