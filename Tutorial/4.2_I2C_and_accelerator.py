from machine import Pin, I2C

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)

MMA845x_ADDR = 0x1C 

def init_sensor():
  i2c.writeto_mem(MMA845x_ADDR, 0x2A, b'\x00')  
  i2c.writeto_mem(MMA845x_ADDR, 0x2A, b'\x01')  

def read_accel():
  
  data = i2c.readfrom_mem(MMA845x_ADDR, 0x01, 6) 
  # extract and process the data
  x = ((data[0] << 8) | data[1]) >> 2
  y = ((data[2] << 8) | data[3]) >> 2
  z = ((data[4] << 8) | data[5]) >> 2

  # convert negative values
  if x > 8191: x -= 16384
  if y > 8191: y -= 16384
  if z > 8191: z -= 16384

  # scale output
  x_g = x / 1024
  y_g = y / 1024
  z_g = z / 1024
  return (x_g, y_g, z_g)

while True:
	x_g, y_g, z_g = read_accel()
  print("X:", x_g, "Y:", y_g,"Z:", z_g)
	sleep(0.2)



