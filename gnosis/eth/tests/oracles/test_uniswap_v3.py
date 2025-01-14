from django.test import TestCase

from eth_account import Account

from ... import EthereumClient
from ...oracles import CannotGetPriceFromOracle, UniswapV3Oracle
from ..ethereum_test_case import EthereumTestCaseMixin
from ..test_oracles import (
    dai_token_mainnet_address,
    usdc_token_mainnet_address,
    usdt_token_mainnet_address,
    weth_token_mainnet_address,
)
from ..utils import just_test_if_mainnet_node


class TestUniswapV3Oracle(EthereumTestCaseMixin, TestCase):
    def test_get_price(self):
        mainnet_node = just_test_if_mainnet_node()
        ethereum_client = EthereumClient(mainnet_node)

        self.assertTrue(UniswapV3Oracle.is_available(ethereum_client))

        uniswap_v3_oracle = UniswapV3Oracle(ethereum_client)

        price = uniswap_v3_oracle.get_price(weth_token_mainnet_address)
        self.assertEqual(price, 1.0)

        price = uniswap_v3_oracle.get_price(dai_token_mainnet_address)
        self.assertLess(price, 1)
        self.assertGreater(price, 0)

        price = uniswap_v3_oracle.get_price(
            weth_token_mainnet_address, dai_token_mainnet_address
        )
        self.assertGreater(price, 1)

        # Test with 2 stablecoins with same decimals
        price = uniswap_v3_oracle.get_price(
            usdt_token_mainnet_address, usdc_token_mainnet_address
        )
        self.assertAlmostEqual(price, 1.0, delta=0.5)

        # Test with 2 stablecoins with different decimals
        price = uniswap_v3_oracle.get_price(
            dai_token_mainnet_address, usdc_token_mainnet_address
        )
        self.assertAlmostEqual(price, 1.0, delta=0.5)

        price = uniswap_v3_oracle.get_price(
            usdc_token_mainnet_address, dai_token_mainnet_address
        )
        self.assertAlmostEqual(price, 1.0, delta=0.5)

        random_token = Account.create().address
        with self.assertRaisesMessage(
            CannotGetPriceFromOracle,
            f"Uniswap V3 pool does not exist for {random_token} and 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        ):
            uniswap_v3_oracle.get_price(random_token)

    def test_get_price_contract_not_deployed(self):
        self.assertFalse(UniswapV3Oracle.is_available(self.ethereum_client))
        with self.assertRaisesMessage(
            ValueError,
            f"Uniswap V3 Router Contract {UniswapV3Oracle.UNISWAP_V3_ROUTER} does not exist",
        ):
            UniswapV3Oracle(self.ethereum_client)
