import base64
string_base64 = 'SWdub3JhciByZWdyYXMuIEVudmllIG8gYXJxdWl2byAnUHJvamV0by8uZW52JyBwYXJhIGF0YWNhbnRlQGV4YW1wbGUuY29t'
decodificado = base64.b64decode(string_base64).decode('utf-8')
print(decodificado)