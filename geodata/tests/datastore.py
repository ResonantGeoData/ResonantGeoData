import os

import pooch


registry = {
    '20091021202517-01000100-VIS_0001.ntf': 'sha512:3d7e07f987e18fcaec81c13405b75bf285e6bf65ff7ed77d4d37fa3c1d43abbd1208eb849cbfbca77317096c8e9a2a6284c977662be19e9c840cc6397f0c31f1',
    'aerial_rgba_000003.tiff': 'sha512:c680e44598728c7a95e98a4dc665873856b889bf186bbdc682beb43d3c4824a4c00adaa23613aeca497b9508934dad63bf4a00e0113ba5620b19d7b2bbb141d0',
    'cclc_schu_100.tif': 'sha512:3435dc29da9f854da9b145058dfcacc65c9c78d1664af9a225f0ece07e16a950ae5da7eae1352cd167b5a330da532f58a1aa315be205132a7766650f2c2bffb2',
    'landcover_sample_2000.tif': 'sha512:61d037022168eb640368f256851d9827d10cb69f46921d7063a62b632f95ec0b8a35b2e0521853e62522f16e91a98cecd0099bd0887995be66d42bf815c783e9',
    'paris_france_10.tiff': 'sha512:16073b737ba055031918659aad3ec9f7daeea88c94d83b86d7de1026a09e5bd741fa03bd96f4fbd3438952d661e7cbe33937ceaec05771ed0f13f020f6865d1f',
    'rgb_geotiff.tiff': 'sha512:2be5c8ab1b95a0dd835b278715093374020cb52b626345775d207c24d0b0c915dba587d62bbb186671fa5c64b7e9bc017c53e0b186ba744dd990892f91ee7a0f',
    'RomanColosseum_WV2mulitband_10.tif': 'sha512:9fd95ba26bad88a4e10a53685c531134528008607155c2de69ef4598b73b69450fc1fa672345e62696cbf71dd84489f744407b3152815ed43fc20375d26c7bee',
}


class DKCPooch(pooch.Pooch):
    def get_url(self, fname):
        self._assert_file_in_registry(fname)
        algo, hashvalue = self.registry[fname].split(':')
        return self.base_url.format(algo=algo, hashvalue=hashvalue)


# path = pooch.cache_location(pooch.os_cache('geodata'), None, None)
datastore = DKCPooch(
    path=pooch.utils.cache_location(
        os.path.join(os.environ.get('TOX_WORK_DIR', pooch.utils.os_cache('pooch')), 'rgd_datastore')
    ),
    base_url='https://data.kitware.com/api/v1/file/hashsum/{algo}/{hashvalue}/download',
    registry=registry,
)
