from time import time

from django.test import TestCase

from eth_account import Account
from web3 import Web3

from ...eth import EthereumNetwork
from ...eth.constants import NULL_ADDRESS
from .. import GnosisProtocolAPI, Order, OrderKind


class TestGnosisProtocolAPI(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gnosis_protocol_api = GnosisProtocolAPI(EthereumNetwork.RINKEBY)
        cls.gno_token_address = "0x6810e776880C02933D47DB1b9fc05908e5386b96"
        cls.weth_token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        cls.rinkeby_dai_address = "0x5592EC0cfb4dbc12D3aB100b257153436a1f0FEa"

    def test_api_is_available(self):
        random_owner = Account.create().address
        for ethereum_network in (
            EthereumNetwork.MAINNET,
            EthereumNetwork.RINKEBY,
            EthereumNetwork.XDAI,
        ):
            with self.subTest(ethereum_network=ethereum_network):
                self.assertEqual(self.gnosis_protocol_api.get_orders(random_owner), [])

    def test_get_estimated_amount(self):
        gnosis_protocol_api = GnosisProtocolAPI(EthereumNetwork.MAINNET)
        response = gnosis_protocol_api.get_estimated_amount(
            self.gno_token_address, self.gno_token_address, OrderKind.SELL, 1
        )
        self.assertDictEqual(
            response,
            {
                "errorType": "SameBuyAndSellToken",
                "description": "Buy token is the same as the sell token.",
            },
        )

        response = gnosis_protocol_api.get_estimated_amount(
            "0x6820e776880c02933d47db1b9fc05908e5386b96",
            self.gno_token_address,
            OrderKind.SELL,
            1,
        )
        self.assertIn("errorType", response)
        self.assertIn("description", response)

        response = gnosis_protocol_api.get_estimated_amount(
            self.gno_token_address, self.weth_token_address, OrderKind.SELL, int(1e18)
        )
        amount = int(response["amount"]) / 1e18
        self.assertGreater(amount, 0)
        self.assertLess(amount, 1)

    def test_get_fee(self):
        order = Order(
            sellToken=self.gno_token_address,
            buyToken=self.gno_token_address,
            receiver=NULL_ADDRESS,
            sellAmount=1,
            buyAmount=1,
            validTo=int(time()) + 3600,
            appData=Web3.keccak(text="hola"),
            feeAmount=0,
            kind="sell",
            partiallyFillable=False,
            sellTokenBalance="erc20",
            buyTokenBalance="erc20",
        )
        self.assertGreaterEqual(self.gnosis_protocol_api.get_fee(order), 0)

    def test_get_trades(self):
        self.assertEqual(
            self.gnosis_protocol_api.get_trades(
                "0x9c79b5883b7f2bacbedef554a835fb07c21f4b1b046edf510554a6ba0444d2665ac255889882acd3da2aa939679e3f3d4ce"
                "a221e72eb7b80"
            ),
            [
                {
                    "blockNumber": 9269212,
                    "logIndex": 0,
                    "orderUid": "0x9c79b5883b7f2bacbedef554a835fb07c21f4b1b046edf510554a6ba0444d2665ac255889882acd3da2aa939679e3f3d4cea221e72eb7b80",
                    "buyAmount": "480792",
                    "sellAmount": "400000000200001",
                    "sellAmountBeforeFees": "1",
                    "owner": "0x5ac255889882acd3da2aa939679e3f3d4cea221e",
                    "buyToken": "0x5592ec0cfb4dbc12d3ab100b257153436a1f0fea",
                    "sellToken": "0xc778417e063141139fce010982780140aa0cd5ab",
                    "txHash": "0x4c888ddeac38b195c9ff7220b61df836a49f8fe2fd9a448da2caf56308db1c61",
                }
            ],
        )

    def test_place_order(self):
        order = Order(
            sellToken=self.gno_token_address,
            buyToken=self.gno_token_address,
            receiver=NULL_ADDRESS,
            sellAmount=1,
            buyAmount=1,
            validTo=int(time()) + 3600,
            appData=Web3.keccak(text="hola"),
            feeAmount=0,
            kind="sell",
            partiallyFillable=False,
            sellTokenBalance="erc20",
            buyTokenBalance="erc20",
        )
        result = self.gnosis_protocol_api.place_order(order, Account().create().key)
        self.assertEqual(
            order["feeAmount"], 0
        )  # Cannot estimate, as buy token is the same as the sell token
        self.assertEqual(
            result,
            {
                "description": "Buy token is the same as the sell token.",
                "errorType": "SameBuyAndSellToken",
            },
        )

        order["sellToken"] = self.gnosis_protocol_api.weth_address
        order["buyToken"] = self.rinkeby_dai_address
        self.assertEqual(
            self.gnosis_protocol_api.place_order(order, Account().create().key),
            {
                "description": "order owner must have funds worth at least x in his account",
                "errorType": "InsufficientBalance",
            },
        )
