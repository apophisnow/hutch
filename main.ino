#include <FastLED.h>
    #define NUM_LEDS 24
    #define DATA_PIN 6
    #define FRAMES_PER_SECOND 60
    #define BRIGHTNESS_PERCENT 50
CRGB leds[NUM_LEDS];

bool stringComplete;
String inputString;

//our command string
#define COMMAND_SIZE 128
  //  char word[COMMAND_SIZE];

void setup() {
    FastLED.addLeds<NEOPIXEL, DATA_PIN>(leds, NUM_LEDS);
    FastLED.setBrightness(map(BRIGHTNESS_PERCENT, 0, 100, 0, 255));
    Serial.begin(9600);
    Serial.println("Starting up...");
    
    // Make sure all LEDs are off.
    for (int i = 0; i < NUM_LEDS; i++){
        leds[i] = CRGB::Black;
    }
    FastLED.show();
}

void loop() {

    if (stringComplete) {
        Serial.print(inputString);
        Serial.print(" ");
        unsigned int count = inputString.length();
        char str_array[count];
        inputString.toCharArray(str_array, count);
        Serial.print(has_command('A',str_array, count));
        // inputString = "";
        stringComplete = false;
    }
    
    switch (inputString[0]) {
        case 'A':
            switch (inputString[1]){
                case '1':
                    a_Red();
                    break;
                case '2':
                    a_Blue();
                    break;
                case '3':
                    a_Pink();
                    break;            
            }
        break;
    }
    /*
    if (inputString == "A1"){
        a_Red();
    }
    if (inputString == "A2"){
        a_Blue();
    }
    if (inputString == "A3"){
        a_Pink();
    }
*/
    inputString = "";

    FastLED.show();
    
    // Use FastLED library delay if possible. Update LEDs according to framerate desired.
    #if defined(FASTLED_VERSION) && (FASTLED_VERSION >= 2001000)
        FastLED.delay(1000 / FRAMES_PER_SECOND);
    #else  
        delay(1000 / FRAMES_PER_SECOND);
    #endif  
}

// This is the same as just reading from serial at the end of loop. May not be ideal in all cases.
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}

//look for the command if it exists.
bool has_command(char key, char instruction[], int string_size)
{
	for (byte i=0; i<string_size; i++)
	{
		if (instruction[i] == key)
			return true;
	}
	
	return false;
}

void a_Red() {
    for (int i = 0; i < NUM_LEDS; i++){
            leds[i] = CRGB(CRGB::Red);
        }
}

void a_Blue() {
    for (int i = 0; i < NUM_LEDS; i++){
            leds[i] = CRGB(CRGB::Blue);
        }
}

void a_Pink() {
    for (int i = 0; i < NUM_LEDS; i++){
            CRGB pink = CHSV( HUE_PINK, 255, 255);
            leds[i] = pink;
        }
}