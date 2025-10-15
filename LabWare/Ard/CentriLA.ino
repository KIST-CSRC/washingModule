int ENA=2;
int IN1=3;
int IN2=4;

void setup()
{
    pinMode(IN1,OUTPUT);
    pinMode(IN2,OUTPUT);
    pinMode(ENA,OUTPUT);
    Serial.begin(9600);
}

void loop()
{
    if  (Serial.available() > 0) {
        
        String input = Serial.readStringUntil('\n'); // '\n'까지 읽습니다.
//        String input = Serial.readString();//      
        input.trim(); // 문자열 양쪽의 공백이나 '\n'을 제거합니다.

        if (input == "close"){
            // 엑추에이터 닫는 동작
            digitalWrite(IN1,HIGH);
            digitalWrite(IN2,LOW);
            analogWrite(ENA,255);
            delay(22000); 
            digitalWrite(IN1, LOW);
            digitalWrite(IN2, LOW);
            analogWrite(ENA, 0);

            Serial.println("close OK"); // 명령어 확인
        }
        else if (input == "open"){
            // 엑추에이터 열기 동작
            digitalWrite(IN1,LOW);
            digitalWrite(IN2,HIGH);
            analogWrite(ENA,255);
            delay(22000);
            digitalWrite(IN1, LOW);
            digitalWrite(IN2, LOW);
            analogWrite(ENA, 0);

            Serial.println("open OK"); // 명령어 확인
        }
        else if (input == "stop"){
            digitalWrite(IN1,LOW);
            digitalWrite(IN2,LOW);
            analogWrite(ENA,0);

            Serial.println("stop OK"); // 명령어 확인
        }
        else if (input == "fullclose"){
            digitalWrite(IN1,HIGH);
            digitalWrite(IN2,LOW);
            analogWrite(ENA,255);

            Serial.println("fullclose OK"); // 명령어 확인
        }
        else if (input == "fullopen"){
            digitalWrite(IN1,LOW);
            digitalWrite(IN2,HIGH);
            analogWrite(ENA,255);

            Serial.println("fullopen OK"); // 명령어 확인
        }
        else {
            Serial.println("Unknown Command"); // 알 수 없는 명령어를 받았을 때의 응답
        }
    }
}
