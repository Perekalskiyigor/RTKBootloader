# RTKBootloader
RTKBootloader


1. Создаем объект стол 1
2. Выводим стол в начальные положения.
3. Обявляем и обнуляем пременные стола1
Регул <- Движение по оси Х влево
Регул <- Движение по оси Х вправо
Регул <- Положение по оси Y вниз
Регул <- Положение по оси Y вверх
Левая сторона стола наличие платы = False
Правая сторона стола наличие платы = False
Команда прошивки = = False
Ответ по прошивке.
Стол занят = False

Начало работы.
Первый цикл только один раз
1. Робот <- Положи плату на стол 1 ложе1 сторона.
2. Робот -> Плату положил.
3. Регул <- Сдвинь плату вправо.
4. Регул -> Сдвинул
4. Робот <- Положи плату на стол 1 ложе2 сторона.
2. Робот -> Плату положил.
2. Регул -> Ничего не делай

Цикл основной
1. Стол 1ложе занят
2. Стол 2ложе занят
5. Регул <- Опусти прошивальщик ложе 2.
6. Регул -> Опустил
7. Сервер <- Начни шить
7. Сервер -> Ответ по прошивке (плохо, хорошо)
8. Регул <- Подними прошивальщик.
6. Регул -> Поднял

3. Регул <- Сдвинь плату освободив ложе1.
4. Регул -> Сдвинул
4. Робот <- Забери плату с ложе 1.
2. Робот -> Плату забрал.
4. Стол 1ложе свободен
4. Робот <- Положи плату ложе 1.
4. Робот -> Плату положил.
4. Стол 1ложе занято
5. Регул <- Опусти прошивальщик (плата на ложе2).
6. Регул -> Опустил
7. Сервер <- Начни шить
7. Сервер -> Ответ по прошивке (плохо, хорошо)
8. Регул <- Подними прошивальщик.
6. Регул -> Поднял


3. Регул <- Сдвинь плату освободив ложе2.
4. Регул -> Сдвинул
4. Стол 2ложе свободен
4. Робот <- Забери плату с ложе 2.
2. Робот -> Плату забрал.
4. Робот <- Положи плату ложе 2.
4. Робот -> Плату положил.
5. Регул <- Опусти прошивальщик ложе1.
6. Регул -> Опустил
7. Сервер <- Начни шить
7. Сервер -> Ответ по прошивке (плохо, хорошо)
8. Регул <- Подними прошивальщик.
6. Регул -> Поднял


3. Регул <- Сдвинь плату освободив ложе1.
4. Регул -> Сдвинул
4. Стол 1ложе свободен
4. Робот <- Забери плату с ложе 1.
2. Робот -> Плату забрал.
4. Робот <- Положи плату ложе 1.
4. Робот -> Плату положил.
5. Регул <- Опусти прошивальщик ложе2.
6. Регул -> Опустил
7. Сервер <- Начни шить
7. Сервер -> Ответ по прошивке (плохо, хорошо)
8. Регул <- Подними прошивальщик.
6. Регул -> Поднял


3. Регул <- Сдвинь плату освободив ложе2.
4. Регул -> Сдвинул
4. Стол 2ложе свободен
4. Робот <- Забери плату с ложе 2.
2. Робот -> Плату забрал.
4. Робот <- Положи плату ложе 2.
4. Робот -> Плату положил.
5. Регул <- Опусти прошивальщик ложе1.
6. Регул -> Опустил
7. Сервер <- Начни шить
7. Сервер -> Ответ по прошивке (плохо, хорошо)
8. Регул <- Подними прошивальщик.
6. Регул -> Поднял

Стол 1ложе свободен