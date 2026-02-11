// Lane 1
int L1_R = 2;
int L1_Y = 3;
int L1_G = 4;

// Lane 2
int L2_R = 5;
int L2_Y = 6;
int L2_G = 7;

// Lane 3
int L3_R = 8;
int L3_Y = 9;
int L3_G = 10;

// Lane 4
int L4_R = 11;
int L4_Y = 12;
int L4_G = 13;

String command = "";

void setup() {
  Serial.begin(9600);

  pinMode(L1_R, OUTPUT);
  pinMode(L1_Y, OUTPUT);
  pinMode(L1_G, OUTPUT);

  pinMode(L2_R, OUTPUT);
  pinMode(L2_Y, OUTPUT);
  pinMode(L2_G, OUTPUT);

  pinMode(L3_R, OUTPUT);
  pinMode(L3_Y, OUTPUT);
  pinMode(L3_G, OUTPUT);

  pinMode(L4_R, OUTPUT);
  pinMode(L4_Y, OUTPUT);
  pinMode(L4_G, OUTPUT);

  allRed();
}

void loop() {
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();
    controlSignal(command);
  }
}

void allRed() {
  digitalWrite(L1_R, HIGH);
  digitalWrite(L2_R, HIGH);
  digitalWrite(L3_R, HIGH);
  digitalWrite(L4_R, HIGH);
}

void controlSignal(String cmd) {

  // Turn all OFF first
  digitalWrite(L1_R, LOW); digitalWrite(L1_Y, LOW); digitalWrite(L1_G, LOW);
  digitalWrite(L2_R, LOW); digitalWrite(L2_Y, LOW); digitalWrite(L2_G, LOW);
  digitalWrite(L3_R, LOW); digitalWrite(L3_Y, LOW); digitalWrite(L3_G, LOW);
  digitalWrite(L4_R, LOW); digitalWrite(L4_Y, LOW); digitalWrite(L4_G, LOW);

  // Lane 1
  if (cmd == "L1_G"){
    digitalWrite(L1_G, HIGH);
    digitalWrite(L2_R, HIGH);
    digitalWrite(L3_R, HIGH);
    digitalWrite(L4_R, HIGH);
  }
 

  // Lane 2
  if (cmd == "L2_G") {
    digitalWrite(L1_R, HIGH);
    digitalWrite(L2_G, HIGH);
    digitalWrite(L3_R, HIGH);
    digitalWrite(L4_R, HIGH);
  }


  // Lane 3
  if (cmd == "L3_G"){
    digitalWrite(L1_R, HIGH);
    digitalWrite(L2_R, HIGH);
    digitalWrite(L3_G, HIGH);
    digitalWrite(L4_R, HIGH);
  } 


  // Lane 4
  if (cmd == "L4_G"){
    digitalWrite(L1_R, HIGH);
    digitalWrite(L2_R, HIGH);
    digitalWrite(L3_R, HIGH);
    digitalWrite(L4_G, HIGH);
  }
}
