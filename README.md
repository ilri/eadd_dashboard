## EADD CCP Dashboard
A dashboard for managing participants in the East African Dairy Development (EADD) Continous Cow Productivity (CCP) survey

## Installation
Clone the project and then execute the command
```
python setup.py install
```

Add a secrets file with the format
```
WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

DBHOST = 'YOUR_HOST'
DBNAME = 'DATABASE_NAME'
DBUSERNAME = 'USERNAME'
DBPASSWORD = 'PASSWORD'
DBPORT = DB_PORT
```

## License
Copyright (C)2016 International Livestock Research Institute (ILRI)

The contents of this repository are free software: you can redistribute
it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

## Authors
Developed by Absolomon Kihara soloincc[at]gmail[dot]com, a consultant for the EADD project
