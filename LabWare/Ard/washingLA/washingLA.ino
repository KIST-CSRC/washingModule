

const int PUL = 7;
const int DIR = 6;
const int ENA = 5;
String command = "";

void setup() {
  pinMode(PUL, OUTPUT);
  pinMode(DIR, OUTPUT);
  pinMode(ENA, OUTPUT);

  // Serial 통신 시작
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()> 0) {
    command = Serial.readStringUntil('\n'); // 줄 끝까지 읽기

    if (command == "WashingHOME") {
      for (int i = 0; i < 5; i++) {
        moveSteps(29400, LOW);  // 앞으로 30,000 스텝
//        delay(100); // 원하는 경우, 움직임 사이에 대기 시간 추가
      }
      Serial.println("complete!!");
    } 
    else if (command == "HOME") {
      for (int i = 0; i < 5; i++) {
        moveSteps(29400, HIGH); // 뒤로 30,000 스텝
//        delay(100); // 원하는 경우, 움직임 사이에 대기 시간 추가
      }
      Serial.println("complete!!");
    }
  }
}

void moveSteps(int steps, int direction) {
  digitalWrite(DIR, direction);
  digitalWrite(ENA, HIGH);
  for (int i = 0; i < steps; i++) {
    digitalWrite(PUL, HIGH);
    delayMicroseconds(100);
    digitalWrite(PUL, LOW);
    delayMicroseconds(100);
  }
}
