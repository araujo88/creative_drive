# creative_drive
 
 Aplicação para upload de arquivo em servidor que integra API feita em Django e GUI feita em PyQt5.

 Instruções de uso:
 1) Instalar bibliotecas com o comando: 
  - pip install -r requirements.txt (sistemas Windows)
  - pip3 install -r requirements.txt (sistemas Unix)
 2) Na pasta raiz, iniciar o servidor Django com o comando: 
  - python manage.py runserver (sistemas Windows)
  - python3 manage.py runserver (sistemas Unix)
 3) Na pasta "PyQt" e em um terminal de comando separado, iniciar a aplicação GUI com o comando: 
  - python CreativeDrive.py (sistemas Windows)
  - python3 CreativeDrive.py (sistemas Unix)
 4) Fazer login com os seguintes dados:
  - Usuário: admin
  - Senha: 1234abcd*
 5) Os uploads feitos através da aplicação estarão disponíveis na pasta "uploads"

*Obs.: O servidor local Django precisa estar rodando ao mesmo tempo que a aplicação GUI.
