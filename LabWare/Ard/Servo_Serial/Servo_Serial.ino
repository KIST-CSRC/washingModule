#include <Servo.h>  // 서보 라이브러리 포함

Servo myservo;  // 서보 객체 생성
String command = "";


void setup() {
  Serial.begin(9600);
  myservo.attach(9);  // 서보모터를 9번 핀에 연결
  myservo.write(0);  // 초기 위치를 0도로 설정 (필요에 따라 수정 가능)
  delay(1000);  // 1초 대기

}
void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available()>0) {
    command = Serial.readStringUntil('\n'); // 줄 끝까지 읽기
    if (command == "DispenseHOME"){
      myservo.write(30);
      
    }
    else if (command == "Aspirate"){
      myservo.write(0);
    }
    else if (command == "Injection"){
      myservo.write(90);
    }
    Serial.println("complete!!");    
    }
}
