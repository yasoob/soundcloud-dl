import pytest

def test_single_url():
	from soundcloud_dl import single_url
	url = 'https://soundcloud.com/macklemore/macklemore-x-ryan-lewis-cant'
	final_result = single_url(url)
	expected = {'upload_date': u'2011/08/15 23:43:15 +0000', 'description': u'', 'title': u"Macklemore X Ryan Lewis - Can't Hold Us Feat. Ray Dalton", 'url': u'https://ec-media.soundcloud.com/jDjABSK4wykr.128.mp3?ff61182e3c2ecefa438cd02102d0e385713f0c1faf3b0339595664f90f00ee153afca11a00a6efda403f98d24d6ecf72dc9ce76849be5dc5d959a4df62021ed59220200917&AWSAccessKeyId=AKIAJ4IAZE5EOI7PA7VQ&Expires=1373055104&Signature=U3GZy6k7fCnG7Q5JyOnoaVANx28%3D', 'ext': u'mp3', 'uploader': u'Macklemore & Ryan Lewis', 'id': 21199445}
	assert final_result['upload_date'] == expected['upload_date']
	assert final_result['description'] == expected['description']
	assert final_result['title'] == expected['title']
	assert final_result['ext'] == expected['ext']
	assert final_result['uploader'] == expected['uploader']
	assert final_result['id'] == expected['id']
	assert final_result['url'].split('?')[0] == expected['url'].split('?')[0]