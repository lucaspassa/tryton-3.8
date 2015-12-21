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

Código Fuente
============

http://hg.tryton.org/

Modulos Argentina
================

http://www.tryton.org.ar/modulos/

Requerimientos para ejecutar servidor y cliente
=============

    * Python 2.7 or later (http://www.python.org/)
    * lxml 2.0 or later (http://lxml.de/)
    * relatorio 0.2.0 or later (http://code.google.com/p/python-relatorio/)
    * Genshi (http://genshi.edgewall.org/)
    * python-dateutil (http://labix.org/python-dateutil)
    * polib (https://bitbucket.org/izi/polib/wiki/Home)
    * python-sql 0.2 or later (http://code.google.com/p/python-sql/)
    * Optional: psycopg 2 or later (http://www.initd.org/)
    * Optional: psycopg2cffi 2.5.0 or later
      (http://github.com/chtd/psycopg2cffi)
    * Optional: MySQL-python (http://sourceforge.net/projects/mysql-python/)
    * Optional: pywebdav 0.9.8 or later (http://code.google.com/p/pywebdav/)
    * Optional: pydot (http://code.google.com/p/pydot/)
    * Optional: unoconv http://dag.wieers.com/home-made/unoconv/)
    * Optional: sphinx (http://sphinx.pocoo.org/)
    * Optional: simplejson (http://undefined.org/python/#simplejson)
    * Optional: cdecimal (http://www.bytereef.org/mpdecimal/index.html)
    * Optional: python-Levenshtein
      (http://github.com/miohtama/python-Levenshtein)
    * Optional: bcrypt (https://github.com/pyca/bcrypt)
    * Optional: mock (http://www.voidspace.org.uk/python/mock/)

Configuración
==========

http://wiki.tryton-erp.es/SAO



