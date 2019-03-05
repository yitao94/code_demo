#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

#include "includes.h"
#include "system.h"

#include "image_sensor.h"
#include "altera_avalon_pio_regs.h"

#include "altera_avalon_spi_regs.h"
#include "altera_avalon_spi.h"

//------------------------------------------------------------
// SPI Handling
//------------------------------------------------------------
uint8_t spi_read(uint32_t base_addr, uint8_t addr){
	uint8_t write = addr;
	uint8_t read = 0;
	alt_avalon_spi_command(base_addr, 0,1, &write,1, &read,0);
	return read;
}

int spi_assert(uint32_t base_addr, uint8_t addr, uint8_t data){
	uint8_t write[3]={0x80+addr,data,addr};
	uint8_t read;

	alt_avalon_spi_command(base_addr, 0,3, write,1, &read,0);
	//printf("%x___%x\n",data,read);
	if (data==read)
		return 1;
	else
		return 0;
}

int image_sensor_init()
{
	uint8_t spi_out=0;
	uint8_t spi_in;
	int i=1;
	int j=1;

	uint16_t addr[64];
	uint16_t data[64];
	uint8_t nCmd = 0;
	addr[nCmd]	=0x72;		//	Addr	114
	data[nCmd++]=0x03;		//	Data	PLL => 5MHz
	addr[nCmd]	=0x6F;      	//	Addr	111 | 0x6F [0]
	data[nCmd++]=0x01;      	//	Data	Bit Mode | 1=10 0=12
	addr[nCmd]	=0x75;      	//	Addr	117 | 0x75 [7:0]
	data[nCmd++]=0x08;      	//	Data	PLL_load | 8=10 4=12

	addr[nCmd]	=0x74;      	//	Addr	116 | 0x74 [3:0]
	data[nCmd++]=0x09;      	//	Data	PLL_div | 9=10 11=12

	printf("Initiate Image Sensor\n");

	// turn off the clock
	IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b00000000);

	// turn on the clock
	IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b10000000);
	for (j=1;j<10;j++){
		;
	}
	// reset
	IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b10000001);


	// turn off sensor at the first beginning
	//IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b00000000); // only the high seventh bit is used for power_en
//	IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0x00); // set 0-th bit one

	// turn on sensor
	//IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b01000000);

	int read_from_out_pin;

	// spi cs on sensor
	IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b10000101);



	read_from_out_pin = IORD_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE);
	printf("read from out pin: %x\n", read_from_out_pin);
	printf("try to turn on the sensor.\n");


	//alt_avalon_spi_command(IMAGE_SENSOR_SPI_BASE, 0,2, 0b1000001100000000,1, &spi_out,0);
	//alt_avalon_spi_command(IMAGE_SENSOR_SPI_BASE, 0,2, 0b1000010000010000,1, &spi_out,0);
	printf("%d\n", spi_out);

//	IOWR_ALTERA_AVALON_PIO_DATA(LED_PIO_BASE, 0x1);

	int time_i;
	// spi
	// read sensor type

	while (i){
		/*
		//spi_out = spi_read(IMAGE_SENSOR_SPI_BASE, 0x7D);
		for (time_i=0;time_i%1000<1000;time_i++){
			if(time_i < 500){
				IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0xf0); // set 0-th bit one
			}
			else{
				IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0xff); // set 0-th bit one
			}

			if(spi_out!=255){
				//printf("%d\n", spi_out);
				;
			}
		}
		*/

		int comm=1;


		//scanf("%d", &comm);
		/*
		if(comm){
			IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b11100011);
		}
		else{
			IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b11100010);
		}
		*/
		printf("%d\n", comm);

/*
		IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b11100111);
		spi_out = spi_read(IMAGE_SENSOR_SPI_BASE, 0x7D); // 7D
		printf("%d\n", spi_out);
		spi_out = spi_read(IMAGE_SENSOR_SPI_BASE, 0x82); // 7D
		printf("%d\n", spi_out);
*/
		spi_out = 0;

		//alt_avalon_spi_command(IMAGE_SENSOR_SPI_BASE, 0,1, 0b00001000,1, &spi_out,0); //try to read rtc 08H
		//spi_out = spi_read(IMAGE_SENSOR_SPI_BASE, 0b10001000); // 7D
		spi_out = spi_read(IMAGE_SENSOR_SPI_BASE, 0x7D); // 7D
		printf("%d\n", spi_out);
        //spi_out = spi_read(IMAGE_SENSOR_SPI_BASE, 0x82); // 7D
		printf("%d\n", spi_out);
	}



	switch (spi_out) {
			case 32: printf("CMV2000v2\n"); break;
			case 35: printf("CMV2000v3\n"); break;
			case 65: printf("CMV4000v2\n"); break;
			case 67: printf("CMV4000v3\n"); break;
			default: printf("unknown device! spi_out: %d\n", spi_out); break;
	}
	printf("try to read spi.\n");


}

int image_sensor_init_2(){
	printf("Initiate Image Sensor\n");

	uint32_t exp = 100; 	//exp time

	uint16_t addr[64];
	uint16_t data[64];

	//Sensor off
	IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b11100110); // set 0-th bit one


	uint8_t nCmd = 0;

	//SPI Command List
	addr[nCmd]	=0x72;		//	Addr	114
	data[nCmd++]=0x03;		//	Data	PLL => 5MHz

	addr[nCmd]	=0x29;		//	Addr	41
	data[nCmd++]=0x04;		//	Data	Exp_ext

	addr[nCmd]	=0x4D;		//	Addr	77
	data[nCmd++]=0x00;		//	Data	Col_calib + ADC_calib

	addr[nCmd]	=0x54;		//	Addr	84
	data[nCmd++]=0x04;		//	Data	I_col

	addr[nCmd]	=0x55;		//	Addr	85
	data[nCmd++]=0x01;		//	Data	I_col_prech

	addr[nCmd]	=0x57;      //	Addr	87
	data[nCmd++]=0x0C;      //	Data	I_amp

	addr[nCmd]	=0x58;      	//	Addr	88
	data[nCmd++]=0x40;      	//	Data	Vtf_l1

	addr[nCmd]	=0x5B;      	//	Addr	91
	data[nCmd++]=0x40;      	//	Data	Vres_low

	addr[nCmd]	=0x5E;      	//	Addr	94
	data[nCmd++]=0x65;      	//	Data	V_prech

	addr[nCmd]	=0x5F;      	//	Addr	95
	data[nCmd++]=0x6A;      	//	Data	V_ref

	addr[nCmd]	=0x76;      	//	Addr	118
	data[nCmd++]=0x01;      	//	Data	Dummy

	addr[nCmd]	=0x7B;      	//	Addr	123
	data[nCmd++]=0x62;      	//	Data	V_blacksun

	addr[nCmd]	=0x28;      	//	Addr	40 | 0x28 [1:0]
	data[nCmd++]=0x00;      	//	Data	image_flipping

	addr[nCmd]	=0x48;      	//	Addr	72
	data[nCmd++]=0x03;      	//	Data	Output Mode = 8/01 [16/00 4/02 2/03]Channel

	//Bit Mode-----------------------------------------------------------------------------------
	addr[nCmd]	=0x6F;      	//	Addr	111 | 0x6F [0]
	data[nCmd++]=0x01;      	//	Data	Bit Mode | 1=10 0=12

	addr[nCmd]	=0x70;      	//	Addr	112 | 0x70 [1:0]
	data[nCmd++]=0x00;      	//	Data	ADC_resolution | 0=10 1=11 2=12

	addr[nCmd]	=0x75;      	//	Addr	117 | 0x75 [7:0]
	data[nCmd++]=0x08;      	//	Data	PLL_load | 8=10 4=12

	addr[nCmd]	=0x74;      	//	Addr	116 | 0x74 [3:0]
	data[nCmd++]=0x09;      	//	Data	PLL_div | 9=10 11=12

	//EXP TIME------------------------------------------------------------------------------------
	addr[nCmd]	=0x2A;      			//	Addr	42
	data[nCmd++]=(exp & 0x0000ff);      //	Data	Exp_time
	addr[nCmd]	=0x2B;      			//	Addr	43
	data[nCmd++]=(exp & 0x00ff00)>>8;   //	Data	Exp_time
	addr[nCmd]	=0x2C;      			//	Addr	44
	data[nCmd++]=(exp & 0xff0000)>>16;  //	Data	Exp_time

	//#Frames-------------------------------------------------------------------------------------
	addr[nCmd]	=0x46;      			//	Addr	70
	data[nCmd++]=0x01;      			//	Data	number of frames [7:0] 01
	addr[nCmd]	=0x47;      			//	Addr	71
	data[nCmd++]=0x00;      			//	Data	number of frames [15:8] 00

	//ADC-----------------------------------------------------------------------------------------
	addr[nCmd]	=0x67;      			//	Addr	103 [7:0]
	data[nCmd++]=0x3C;      			//	Data	ADC GAIN 20

	addr[nCmd]	=0x79;      			//	Addr	121 [0]
	data[nCmd++]=0x03;      			//	Data	black_col + PGAx2

	addr[nCmd]	=0x66;    				//	Addr	102 [1:0]
	data[nCmd++]=0x03;      			//	Data	PGA

	//Vramp---------------------------------------------------------------------------------------
	addr[nCmd]	=0x62;      			//	Addr	98
	data[nCmd++]=0x66;      			//	Data	V_ramp1 60
	addr[nCmd]	=0x63;      			//	Addr	99
	data[nCmd++]=0x66;      			//	Data	V_ramp2 60

	//Offset--------------------------------------------------------------------------------------
	//2's Comp. 0=0 8191=8191 <> 8193=-8191 16383=-1
	addr[nCmd]	=0x64;      			//	Addr	100 [7:0]
	data[nCmd++]=0xC3;      			//	Data	Offset C3
	addr[nCmd]	=0x65;      			//	Addr	101 [5:0]
	data[nCmd++]=0x3F;      			//	Data	Offset 3F




	//Sensor On
	IOWR_ALTERA_AVALON_PIO_DATA(OUT_PIO_BASE, 0b11100111); // set 0-th bit one

	//SPI--------------------------------------------------------
	int out;
	out = spi_read(IMAGE_SENSOR_SPI_BASE,0x7D);
	switch (out) {
		case 32: printf("CMV2000v2\n"); break;
		case 35: printf("CMV2000v3\n"); break;
		case 65: printf("CMV4000v2\n"); break;
		case 67: printf("CMV4000v3\n"); break;
		default: printf("unknown device!  %d\n",out); break;
	}

	int i;
	for( i=0;i<nCmd;i++){
		if(!spi_assert(IMAGE_SENSOR_SPI_BASE,addr[i],data[i])){
			printf("SPI Error on command %i\n",i);
			return 0;
		}
	}

	printf("EXP: %d\n",(int)exp);

	//printf("Buffer address set to 0x%lx\n",(uint32_t)IORD(VIDEO_DMA_CONTROLLER_0_BASE, 1));



	printf("\nImage Sensor Setup\n");

	return 0;
}

