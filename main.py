from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import struct
import os

app = FastAPI(
    title="Calculator PZ1 - Architecture of Computers",
    description="API для автоматизації розрахунків до ПЗ1 (Системи числення, IEEE 754, ASCII)",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

# --- Моделі даних для запитів ---

class ConvertIntRequest(BaseModel):
    number: str
    from_base: int
    to_base: int

class ConvertFractionRequest(BaseModel):
    number: str
    from_base: int
    to_base: int
    precision: int = 5  # Точність (кількість знаків після коми)

class ArithmeticRequest(BaseModel):
    a: int
    b: int
    operation: str  # "add", "sub", "mul"

class IEEE754Request(BaseModel):
    number: float

class ASCIIRequest(BaseModel):
    text: str

# --- Ендпоінти (Функції) ---

@app.post("/api/convert_integer", summary="Переведення цілих чисел", tags=["Системи числення"])
def convert_integer(request: ConvertIntRequest):
    """
    Переводить ціле число з однієї системи числення в іншу.
    Підтримуються системи: 2, 8, 10, 16.
    """
    try:
        decimal_value = int(request.number, request.from_base)
        if request.to_base == 10:
            result = str(decimal_value)
        elif request.to_base == 2:
            result = bin(decimal_value)[2:]
        elif request.to_base == 8:
            result = oct(decimal_value)[2:]
        elif request.to_base == 16:
            result = hex(decimal_value)[2:].upper()
        else:
            raise HTTPException(status_code=400, detail="Підтримуються тільки бази 2, 8, 10, 16")
        return {
            "input": request.number,
            "from_base": request.from_base,
            "to_base": request.to_base,
            "result": result,
            "decimal_value": decimal_value
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Некоректне число для заданої системи числення")

@app.post("/api/convert_fraction", summary="Переведення дробових чисел", tags=["Системи числення"])
def convert_fraction(request: ConvertFractionRequest):
    """
    Переводить дробове число з однієї системи в іншу (2, 8, 10, 16).
    """
    num_str = request.number.replace(',', '.')
    if '.' not in num_str:
        num_str += ".0"

    parts = num_str.split('.')
    integer_part = parts[0]
    fraction_part = parts[1]

    try:
        dec_int = int(integer_part, request.from_base)

        dec_frac = 0.0
        for i, digit in enumerate(fraction_part):
            val = int(digit, request.from_base)
            dec_frac += val * (request.from_base ** -(i + 1))

        full_decimal = dec_int + dec_frac

        if request.to_base == 10:
            return {"result": str(full_decimal)}

        if request.to_base == 2:
            res_int = bin(dec_int)[2:]
        elif request.to_base == 8:
            res_int = oct(dec_int)[2:]
        elif request.to_base == 16:
            res_int = hex(dec_int)[2:].upper()
        else:
            res_int = str(dec_int)

        res_frac = ""
        current_frac = dec_frac

        for _ in range(request.precision):
            current_frac *= request.to_base
            digit = int(current_frac)

            if digit >= 10:
                res_frac += chr(ord('A') + digit - 10)
            else:
                res_frac += str(digit)

            current_frac -= digit
            if current_frac == 0:
                break

        return {"result": f"{res_int}.{res_frac}"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Некоректне дробове число")

@app.post("/api/binary_arithmetic", summary="Арифметика (2-кова система)", tags=["Арифметика"])
def binary_arithmetic(request: ArithmeticRequest):
    """
    Виконує додавання, віднімання або множення двох десяткових чисел,
    але повертає результат у двійковій системі (як вимагається в завданні).
    """
    a, b = request.a, request.b
    if request.operation == "add":
        res_dec = a + b
    elif request.operation == "sub":
        res_dec = a - b
    elif request.operation == "mul":
        res_dec = a * b
    else:
        raise HTTPException(status_code=400, detail="Операція повинна бути 'add', 'sub' або 'mul'")

    res_bin = bin(res_dec)[2:] if res_dec >= 0 else "-" + bin(abs(res_dec))[2:]
    return {"result_bin": res_bin, "result_dec": res_dec}


@app.post("/api/ieee754", summary="Конвертація в IEEE 754 (32-bit)", tags=["IEEE 754"])
def float_to_ieee754(request: IEEE754Request):
    """
    Переводить дробове число у формат IEEE 754 Single Precision (32 біти).
    Повертає бінарне представлення та HEX.
    """
    # struct.pack пакує float у 4 байти (формат 'f'), '!' означає network order (big-endian)
    packed = struct.pack('!f', request.number)
    integers = [b for b in packed]
    binary_str = ''.join(f'{b:08b}' for b in integers)
    hex_str = packed.hex().upper()
    return {
        "binary": f"{binary_str[0]} {binary_str[1:9]} {binary_str[9:]}",
        "hex": hex_str,
    }

@app.post("/api/ascii", summary="Кодування тексту в ASCII", tags=["Кодування"])
def ascii_encoder(request: ASCIIRequest):
    """
    Кодує введений текст (наприклад, прізвище) у коди ASCII (DEC, HEX, BIN).
    """
    result = []
    for char in request.text:
        code = ord(char)
        result.append({
            "char": char,
            "dec": code,
            "hex": hex(code)[2:].upper(),
            "bin": bin(code)[2:].zfill(8)
        })
    return {"data": result}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)