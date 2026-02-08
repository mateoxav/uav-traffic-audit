from bitsv import Key

# 1. Indicar 'test' AL CREAR la clave
k_new = Key(network='test') 

# 2. Ahora al exportar, la WIF tendrá el prefijo correcto
wif_test = k_new.to_wif()

print("WIF Correcta (Testnet):", wif_test) 
# Debería empezar por 'c', ej: cMjQu...

print("Dirección:", k_new.address)
# Debería empezar por 'm' o 'n'