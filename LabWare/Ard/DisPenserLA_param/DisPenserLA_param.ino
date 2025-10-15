const int PUL = 7;
const int DIR = 6;
const int ENA = 5;
String command = "";

void setup() {
  pinMode(PUL, OUTPUT);
  pinMode(DIR, OUTPUT);
  pinMode(ENA, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('\n');

    int index_of_comma = command.indexOf(',');
    String cmd = command.substring(0, index_of_comma);
    cmd.trim(); // Remove any leading or trailing whitespace
    String step_str = command.substring(index_of_comma+1);
    step_str.trim(); // Remove any leading or trailing whitespace

    long steps = step_str.toInt();
    
    if (cmd == "DOWN") {
      moveSteps(steps, LOW);
      Serial.println("complete!!");
    } 
    else if (cmd == "UP") {
      moveSteps(steps, HIGH);
      Serial.println("complete!!");
    }
  }
}

void moveSteps(long steps, int direction) {
  digitalWrite(DIR, direction);
  digitalWrite(ENA, HIGH);
  for (long i = 0; i < steps; i++) {
    digitalWrite(PUL, HIGH);
    delayMicroseconds(100);
    digitalWrite(PUL, LOW);
    delayMicroseconds(100);
  }
}
