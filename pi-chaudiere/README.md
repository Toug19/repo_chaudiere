installer apache2
générer un certificat ssl2 autocertifié:
  dpkg -l openssl
  sudo mkdir /etc/apache2/ssl
  cd /etc/apache2/ssl/
  sudo openssl genrsa -out rpi-key.pem 2048
  nano configuration.cnf
  sudo nano configuration.cnf
  sudo openssl req -new -x509 -days 365 -key rpi-key.pem -config configuration.cnf -out rpi-certif.pem



emplacement fichier: etc/apache2/sites-available/mytougraspberry.ddns.net.conf
sudo a2enmod proxy_http
sudo a2ensite mytougraspberry.ddns.net.conf


