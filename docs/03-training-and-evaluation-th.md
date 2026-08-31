# วิธี Train และ Evaluate

## Dataset ที่ใช้ train

ใช้เฉพาะ target ที่ยืนยันสถานะได้:

- `validated_positive`: target มีช่องโหว่จริง
- `validated_negative`: target ไม่ vulnerable ต่อ candidate นั้น

ไม่ใช้:

- `inconclusive`: หลักฐานไม่พอ

## Stage 1: Exploitability Gate

งานของ Gate คือ binary classification:

```text
input: target-level scanner features
output: exploit / no_exploit
```

label:

```text
1 = validated_positive
0 = validated_negative
```

model:

```text
XGBoost binary:logistic
```

## Stage 2: Family Ranker

งานของ Ranker คือจัดอันดับ exploit family:

```text
input: target + candidate family features
output: ranked candidate families
```

ใช้เฉพาะ `validated_positive`

label:

```text
1 = candidate family ที่ถูกต้อง
0 = candidate family อื่น
```

model:

```text
XGBoost rank:pairwise
```

## Evaluation

เนื่องจาก dataset ยังเล็ก จึงใช้ leave-one-target-out evaluation

วิธีนี้คือ:

```text
วนทีละ target
เอา target หนึ่งตัวออกมาเป็น test
ใช้ target ที่เหลือ train
ทำซ้ำจนทุก target ได้เป็น test
```

ข้อดี:

- target ทุกตัวถูกทดสอบ
- ลดปัญหา split แล้ว test set เล็กเกินไป
- เหมาะกับ dataset ช่วงเริ่มต้น

ข้อจำกัด:

- ถ้า target คล้ายกันมาก model อาจยังดูดีเกินจริง
- ยังไม่แทน unseen real-world test

## Metrics

### Gate metrics

- `Accuracy`: ทายถูกทั้งหมดกี่เปอร์เซ็นต์
- `Precision`: ที่บอก exploit นั้นถูกจริงกี่เปอร์เซ็นต์
- `Recall`: target ที่มีช่องโหว่จริงถูกจับได้กี่เปอร์เซ็นต์
- `F1`: ค่าเฉลี่ยระหว่าง precision และ recall
- `False Positive`: ไม่มีช่องโหว่แต่ model บอก exploit
- `False Negative`: มีช่องโหว่แต่ model บอก no_exploit

ในงานนี้ให้ความสำคัญกับ Recall และ False Negative ก่อน เพราะการข้ามช่องโหว่จริงเสียหายกว่าการยิงเกิน

### Ranker metrics

- `Top-1`: candidate อันดับแรกถูกไหม
- `Top-3`: candidate ที่ถูกอยู่ใน 3 อันดับแรกไหม
- `MRR`: ค่าเฉลี่ยตำแหน่งคำตอบที่ถูก ยิ่งใกล้ 1 ยิ่งดี
- `Mean Attempts`: โดยเฉลี่ยต้องลองกี่ครั้งถึงเจอคำตอบถูก

## Threshold tuning

Gate ใช้ score จาก 0 ถึง 1 แล้วเลือก threshold

ตัวอย่าง:

```text
score >= 0.20 → exploit
score < 0.20 → no_exploit
```

v0.2 เลือก threshold 0.20 เพราะ:

- Recall = 1.000
- False Negative = 0
- False Positive = 0
- F1 = 1.000

