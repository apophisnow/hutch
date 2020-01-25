#include <FastLED.h>
    #define NUM_LEDS 24
    #define DATA_PIN 6
    #define FRAMES_PER_SECOND 60
    #define BRIGHTNESS_PERCENT 50
CRGB leds[NUM_LEDS];
bool FLASH_IGNORES_BRIGHTNESS=true;

bool stringComplete;
String inputString;
int milliseconds = millis();
String cmd;
bool cmdStart = true;

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

    // Got a new command
    if (stringComplete) {
        //Serial.println(inputString);
        milliseconds = millis();
        cmdStart = true;
        cmd = inputString;
        inputString = "";
        stringComplete = false;
    }
    
    switch (cmd[0]) {
        // Animations: A
        case 'A':
            switch (cmd[1]){
                case '1':
                    if (cmdStart){
                        a_Flashbang(milliseconds, 255);
                        cmdStart = false;
                    }
                    else{
                        a_Flashbang(milliseconds, 0);
                    }
                    break;
                case '2':
                    byte intensity = getMagnitude(cmd);
                    a_Flashbang_live(intensity);
                    break;     
            }
        // Colors: C
        case 'C':
            switch (cmd[1])
                case '1':
                        c_Red();
                        break;
                    case '2':
                        c_Blue();
                        break;
                    case '3':
                        c_Pink();
                        break;
        break;
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

byte getMagnitude(String command){
    return byte(command.substring(3,6).toInt());
}

void c_Red() {
    for (int i = 0; i < NUM_LEDS; i++){
            leds[i] = CRGB::Red;
        }
}

void c_Blue() {
    for (int i = 0; i < NUM_LEDS; i++){
            leds[i] = CRGB::Blue;
        }
}

void c_Pink() {
    for (int i = 0; i < NUM_LEDS; i++){
            CRGB pink = CHSV( HUE_PINK, 255, 255);
            leds[i] = pink;
        }
}

//animations
void a_Flashbang(int startMillis, byte startIntensity) {
    // Simulated flashbang
    if (startIntensity > 0){
        for (int i = 0; i < NUM_LEDS; i++){
            leds[i] = CHSV(0,0,startIntensity);
        }
    }
    else {
        if (millis() - startMillis > 1500) {
            fadeToBlackBy(leds, NUM_LEDS, 64);
        }
    }
    if (FLASH_IGNORES_BRIGHTNESS){
        if (leds[0]) {
            FastLED.setBrightness(map(100, 0, 100, 0, 255));
        }
        else {
            FastLED.setBrightness(map(BRIGHTNESS_PERCENT, 0, 100, 0, 255));
        }
    }
}

void a_Flashbang_live(byte intensity) {
    // Live flashbang that takes constant data from the game state.
    for (int i = 0; i < NUM_LEDS; i++){
        leds[i] = CHSV(0,0,intensity);
    }
    if (FLASH_IGNORES_BRIGHTNESS){
        if (leds[0]) {
            FastLED.setBrightness(map(100, 0, 100, 0, 255));
        }
        else {
            FastLED.setBrightness(map(BRIGHTNESS_PERCENT, 0, 100, 0, 255));
        }
    }
}