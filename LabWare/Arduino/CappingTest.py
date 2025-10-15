import serial
import time

# 시리얼 포트 연결 설정
# Arduino가 연결된 COM 포트와 바우드레이트를 설정하세요.
ser = serial.Serial('/dev/ttyCapping', 115200, timeout=1)
time.sleep(2) # Arduino가 재시동되는 것을 방지하기 위한 초기 대기 시간

while ser.in_waiting:
    ser.readline()

try:
    while True:
        # 사용자로부터 데이터 입력 받기
        user_input = input("Enter a message for the Arduino: ")
        ser.write(user_input.encode()) # 입력 받은 데이터를 인코딩하여 Arduino로 전송
        time.sleep(1) # Arduino로부터 응답을 기다림

        # Arduino로부터 데이터 읽기
        while ser.in_waiting:
            incoming_data = ser.readline().decode('utf-8').rstrip() # 응답 받기
            print(f"Arduino says: {incoming_data}")

except KeyboardInterrupt:
    print("Program terminated by user")
finally:
    ser.close() # 시리얼 포트 정리