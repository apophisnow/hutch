/*

void a_Flashbang(int startMillis, byte startIntensity) {
    // TODO: Needs to be full brightness for about 3 seconds and then fade quickly.
    if (startIntensity){
        for (int i = 0; i < NUM_LEDS; i++){
            leds[i] = CHSV(0,255,startIntensity);
        }
    }
    else {
        if (millis() - startMillis > 3000) {
            fadeToBlackBy(leds, NUM_LEDS, 10);
        }
    }
}
*/