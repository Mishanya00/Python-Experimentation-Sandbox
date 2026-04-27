import segno

qrcode = segno.make_qr("https://www.example.com")
qrcode.save("images/segno_qr.png", scale=10, dark="darkgreen")