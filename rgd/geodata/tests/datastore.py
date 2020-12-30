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
    'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif': 'sha512:b0b52a537d79460afa63a4849c2c03cf686b6f32446a2c56320027f7e701965b0f2af31e0dd843471bc98eecd5f0dd1be67d8c38b4759a81a5a0aa707ae4fea6',
    'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band2.tif': 'sha512:492e30b6fdeebf67332d87ab07258c6bed1f9830c214492866bbd2f06f53fcba72b4984709cd4a486f49a4f1a5effaf482cda95f1456d6e3b7e693bee8d9c200',
    'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band3.tif': 'sha512:adf8114c240ad6d5462fcac0b480cabc827da3b095620741c4eb414da400c368a8f112a6f13470870e86cbefed6235efac6c3611bd3efd53dd6e12114006af56',
    'Streams.zip': 'sha512:7b1469d6e039185183b31a8e0eed90940e1a4db63604673322160b3df2da813652596ddf961ff09a8433b18ce944ae1602b625d5572019ce18bf595c983bc358',
    'Watershedt.zip': 'sha512:8a970437ca0b9b4df7b25c3346f2bd41a133dba2ef0e7d6a2361f982d54a9db2f57979d5ef66284017a77ce630beaede77f95af037749ed2e15604c91b5d8037',
    'demo.kwcoco.json': 'sha512:04f915e2fe66aed5ec1aeb6b13734f9cb546308417656d1b74d870e54e737446f17be5c0996cadef2ce4e7c2778aa695cfe7cb7bc18b114c296b1fdf2a8afed0',
    'demodata.zip': 'sha512:97afa8686ded070ecf68e71bfa2bbee91ac0a8a47d5c175ba940735a0a49ef22b9610aa9ab98464f395fcd6f51945fa41a96a2a331ac593feb4704ca7d98f899',
    'demo_rle.kwcoco.json': 'sha512:f685da33ce8d965aa666cdd957e8b5f6880be3b90c1b8c16c885e0c46eebadb1c059df720e4575e59606dea8ac7b294df22ce5c6c0631bdf636af7229118bbdd',
    'demo_rle.zip': 'sha512:bafa7951f6498ed7363bd28eedd3f14b7fb206abee6791c3dff2b2696066ac46e297f80b663692444d1a60c1d6aa5d4acb7c5109ead52007f037d4c6cf94e068',
    'subset_metadata.klv': 'sha512:4f5dfa60119027b41351c81b9c74804afc7c3b768bdc7687300f779ec35443a81e5a0a8dfa2769de84d4abf240960688e674ade15981788de078579fe8dc9b5a',
    'test_fmv.ts': 'sha512:f9ee5180adc0da3d213baff218e55ab5f5a0b2b75dd71d79048aecaf3ebc3b4611a5123e15bab571b5f9cb11f5dd140d585ef623ffb4de0a6ae8c5ca1a27d847',
    'Elevation.tif': 'sha512:44587c3b00d349344bcec5cefd3bcda9fcef5e9bbdd0f1a2a4ce76016fa0bb68436ac206c96f54d6a828b45db212aa9d43410dbf40a61ba1d8eec934f7070250',
    'MuniBounds.zip': 'sha512:506a6956a37eea9663abd4344535d0c6e44411ab4af97fedd1b7e678b47e8e43397538ae44575fd28d0f8cac760ce4fc7f538e32055c48115996043afabfd165',
    'lm_cnty.zip': 'sha512:7518d92b6e84c8363182f637a9fa9d323abb5d6eab6e4f0d458c522f5e4098e4a38bd2aab5c9dc43c41356aa67f4ab7ed6179aa39da43bb00895641514793cd1',
    'dlwatersan.zip': 'sha512:24bb7df972e01912742f3e3d3b9ba2d679709630f43c64c6fb0b35ad344f778837547ba9e1b54be4702fe31381ee20a6cb0466c9b5f1c53a320fa586626e3b81',
    'dlschool.zip': 'sha512:3a691f1ec170a511fe3d3a856984dbd37016806eda6a73a5ee0e6ba9049e4efbf40b139569295c5efba865f4035249656b5d870ebbd5dfe3df9ed755f2467ac8',
    'dlpark.zip': 'sha512:92719b8ca74f489320becd7f9c6eb42a40ff020dc05886edb3e505cf461efe84ec3bea59571a27c1562f3b7db81c91bf1c01ea8a0d860ddc2e77d2528ab23a09',
    'dlmetro.zip': 'sha512:bc239503ac4b299c805dd0e550015aa97b984f432a25108528d9e1db162ea23302d154197c45e27afaa923cdaee3603b44653880048d2866dc29d93dc0b4aa4d',
    'dllibrary.zip': 'sha512:55d6fbd275084b553cabba6b7fa2bd2ac9fa9305dbe10a68c8c1d93e29ac0b2f4541ca928dc24229df9bc58424f4d087362844711ab7250649eb2912192b642c',
    'dlhospital.zip': 'sha512:9315629e36a3941c4d521741123d6a556647ba0c28ef15928a459d44390cf6e381008a4a3b304de30c0eb3fb5c9fb067fa971aed69656ce9e07632a980c593e1',
    'dlfire.zip': 'sha512:c62c7af20ea356ed7e5b2d236074b82f73eae4313b8020495c306037814eeb7bd5dac086e6b35b66c7cfd08e61b22c43a272f7e1ecc218bf7e8139ecf27e23de',
    'Solid_Mineral_lease_1.zip': 'sha512:a86e5389416f8d7378e337b39dc33cd85c159575e6f87ef5519bd583ce27c936b638e6f1636e5b3907a112618d416b5637f77c70f3272180ac11fd31cc27ae45',
    'AG_lease.zip': 'sha512:3f65183ee7356cbfa72b727f3877d56ad199a18a7e2ae9d869ee2089174da3ffd65060c7a170314f77ceeaca0e8e77b3482209f497d303c8323d335a35f1b317',
    'L1C_T13SCD_A019901_20201227T175922.tif': 'sha512:83d6f87e8ff245702a614357c416a2cda62ad385ac15abed1bd8becfb975b8773fb503b21a5e3d909812392f28bc16d0f55b8a2e8cc47abb8745895ec17b6783',
    'L1C_T18TWN_A016525_20200505T155731.tif': 'sha512:2e4dafda12a7b9ae9098c8bb0cb2d9807a3252cacea649e6bff48932fc4bbb6522a91b2c2de8d3d29c472d964cd3db6ec9848fc47ba2fe5b74d8744ef7690aca',
    'L1C_T18TWN_A018527_20200922T155115.tif': '7e46f45e548b57d907df21a1993c93f9a272679aaf8b0afcbc53e35a2ba7e9a29e2ec3315ce348efe83d60f5f2ffec611da65d6fef71c7d9a05ea395dd79ec88',
    'L1C_T18TWN_A025648_20200520T155359.tif': 'sha512:f1f65c924173610ea01e831ac8139994953d687612a5b4d0bb895db7837d8ba0d012f3ffa04919d21ff20c5d0181270a22b17df29df819bd7e248892a6bc28d1',
    'L1C_T18TWN_A027793_20201017T155552.tif': 'sha512:61a59f37b0af8e3326fd8c189fa868d48460d5ba92b47b0bc8051b76b57e05cc51c76484fb2f4e260119e1870c3d46a6cd05a4da2a022455e251e45a7a9f29e9',
    'L1C_T18TWN_A028079_20201106T160014.tif': 'sha512:68c3cce4033f2b18933ce60fd05bd3602a56c0b8f42d7e774f1af2c07581af485e76c03ce6b82d44eeb7443f60b7bb4fd14834e4bee2f74927b67b05313bf712',
    'bpasg_emodis_week34_082320.tif', 'sha512:70f6ce20a7ff047a6c59e0aed70127a8a1674568108473f757aa80e652092b7cc4584f507d5c630db0b7e1da4f615dea987a4d8eda5bbd720131cd4903c09ca0',
    'vegdri_diff_2020_34_gtif.tif', 'sha512:402dd8ce99ee2352dc6b1400bd9fae599675715c8b5b96d3d691cfdf7d5a04883cedec8e546481ae7d3a0ea1d500cef9b75045a3a9c8270b191ba1c3fe5cb4e9',
    'vegdri_emodis_week34_082320.tif': 'sha512:fe8f9b1738c7e2bc4dc208701051b1f6ce7638305e567c1b088976740d3bb2fa176647460800bc03e3d7e39fd61b62318e7ce3f0752d7aac25700ebda711c17e',
    'US_eMAH_NDVI.2020.350-356.1KM.VI_ACQI.006.2020359165956.tif': 'sha512:14ad91d12d8ea58352b6b2fc51d06ad9fea70488c28c85240c2b60c8fc7fcdd9866bf1d6a73817699acebe8a171a6639bc259a4bcdefbf4f52073a8e84b4b52a',
    'US_eMAH_NDVI.2020.350-356.1KM.VI_NDVI.006.2020359165956.tif': 'sha512:abb5faef4217606356e9bf4ac7bf5927f6d6af4febf1ecb70d88f732b21f1895bfa7ef9dcc3529e0ed2ccebfaced2790f7dc0195abe7c5984a932bcf75180770',
    'US_eMAH_NDVI.2020.350-356.1KM.VI_QUAL.006.2020359165956.tif': 'sha512:1aeb79fef9650d7b6b7993ced40615f82559e5c17da48893a801769a9e78c2bf1576a44340a251f369b62869983770c99b50ac3d38e6cae56ef6424437463f4e',
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
