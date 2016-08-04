# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Contact Google API',
    'version': '0.1',
    'category': '',
    'summary': "Google require a registred API-key for use of maps",
    'description': """
    TODO:
    * Lat, lng in res.company
    * API-key, position, title in javascript
    * Replace old map in contact page
    * javascript code
    <div class="col-md-12" id="google_map" style="max-width: 340px; width: 100%; height: 320px;"></div>
    <script>
      function initMap() {
        var myLatLng = {lat: 59.3425931, lng: 18.038969};
        var map = new google.maps.Map(document.getElementById('google_map'), {
          zoom: 16,
          center: myLatLng
        });
        var marker = new google.maps.Marker({
          position: myLatLng,
          map: map,
          title: 'Your Company'
        });
      }
    </script>
    <script async="async" defer="defer"
        src="https://maps.googleapis.com/maps/api/js?key=MY_API_KEY&amp;callback=initMap">
    </script>

""",
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['website_crm', 'base_geolocalize'],
    'data': [
        'res_config.xml',
    ],
    'application': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
