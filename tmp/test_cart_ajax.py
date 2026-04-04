import json
from django.test import Client
c = Client()
print('Testing update-cart (AJAX POST)')
res = c.post('/update-cart/1/', data=json.dumps({'quantity': 2}), content_type='application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest', SERVER_NAME='127.0.0.1')
print('status:', res.status_code)
print('content:', res.content)

print('\nTesting remove-from-cart (AJAX GET)')
res2 = c.get('/remove-from-cart/1/', HTTP_X_REQUESTED_WITH='XMLHttpRequest', SERVER_NAME='127.0.0.1')
print('status:', res2.status_code)
print('content:', res2.content)
