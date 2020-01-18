#include <FastLED.h>
    #define NUM_LEDS 24
    #define DATA_PIN 6
    #define FRAMES_PER_SECOND 60
    #define BRIGHTNESS_PERCENT 20
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
        int count = inputString.length;
        Serial.print(has_command('A',inputString, count));
        inputString = "";
        stringComplete = false;
    }
    
    if (millis() % 1000 == 0){
        a_Red();
    }
    if (millis() % 2200 == 0){
        a_Blue();
    }


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