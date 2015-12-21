# Tryton ERP 3.8 (Argentina)

http://tryton.org/

http://www.tryton.org.ar/

http://doc.tryton.org/3.8/

#Archivo de Configuración:

Para generar super_pwd (contraseña para administracion de parametros de configuración del servidor)
python -c 'import getpass,crypt,random,string; print crypt.crypt(getpass.getpass(), "".join(random.sample(string.ascii_letters + string.digits, 8)))'

/etc/trytond.conf


#Ejecutar servidor:

trytond -c ../etc/trytond.conf --logconf ../etc/trytondlogs.conf


