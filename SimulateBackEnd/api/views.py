import json

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .serializers import *
from .models import *


@csrf_exempt
def create_transfer(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        address = data['address']
        spend_coin_id = data['spend_coin_id']
        receive_coin_id = data['receive_coin_id']
        spend_amount = data['spend_amount']

        account = Account.objects.get(address=address)
        spend_coin = Coin.objects.get(id=spend_coin_id)
        receive_coin = Coin.objects.get(id=receive_coin_id)

        connector = Connector()

        if spend_coin.is_ETH:
            connector = Connector.objects.get(deposit_coin=spend_coin, smart_coin=receive_coin)
        elif spend_coin.is_bancor:
            if receive_coin.is_ETH:
                connector = Connector.objects.get(smart_coin=spend_coin, deposit_coin=receive_coin)
            else:
                connector = Connector.objects.get(smart_coin=receive_coin, deposit_coin=spend_coin)

        if not account.is_balance_enough(spend_coin, spend_amount):
            return JsonResponse({
                'errmsg': '余额不足'
            }, status=400)

        transfer = account.create_transfer(connector, spend_amount,
                                           is_buying_smart=connector.smart_coin.id is receive_coin.id)

        fake_account = Account.objects.get(address="000000000000000000000000000000000000000000")
        for other_connector in Connector.objects.exclude(id=connector.id):
            fake_account.create_transfer(other_connector, 0, is_buying_smart=True)

        connector_ETH_YMHC = Connector.objects.get(id=1)
        connector_YMHC_LYB = Connector.objects.get(id=2)

        last_YMHC = CoinPriceLog.objects.filter(coin_id=2)[len(CoinPriceLog.objects.filter(coin_id=2)) - 1].value_by_ETH
        last_LYB = CoinPriceLog.objects.filter(coin_id=3)[len(CoinPriceLog.objects.filter(coin_id=3)) - 1].value_by_ETH

        CoinPriceLog.objects.create(value_by_ETH=connector_ETH_YMHC.after_price,
                                    change_rate=(connector_ETH_YMHC.after_price - last_YMHC)
                                                / last_YMHC, coin_id=2)
        CoinPriceLog.objects.create(value_by_ETH=connector_ETH_YMHC.after_price * connector_YMHC_LYB.after_price,
                                    change_rate=(connector_ETH_YMHC.after_price * connector_YMHC_LYB.after_price
                                                 - last_LYB) / last_LYB, coin_id=3)

        return JsonResponse(TransferSerializer(transfer).data, safe=False)

    else:
        return JsonResponse(None, status=400)


@csrf_exempt
def getCoinPriceLog(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        coin_id = data['coin_id']

        logs = CoinPriceLog.objects.filter(coin_id=coin_id)

        return JsonResponse(CoinPriceLogSerializer(logs, many=True).data, safe=False)


@csrf_exempt
def transfer(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        address = data['address']
        target_address = data['target_address']
        spend_coin_id = data['spend_coin_id']
        spend_amount = data['spend_amount']

        account = Account.objects.get(address=address)
        spend_coin = Coin.objects.get(id=spend_coin_id)


@csrf_exempt
def get_balance(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        address = data['address']

        balances = Balance.objects.filter(address__address=address)

        return JsonResponse(BalanceSerializer(balances, many=True).data, safe=False)


@csrf_exempt
def get_connector(request):
    if request.method == 'GET':
        connectors = Connector.objects.all()

        return JsonResponse(ConnectorSerializer(connectors, many=True).data, safe=False)


@csrf_exempt
def get_rate(request):
    connector_ETH_YMHC = Connector.objects.get(id=1)
    connector_YMHC_LYB = Connector.objects.get(id=2)

    ret = [
        [1, 1 / connector_ETH_YMHC.after_price, 1 / (connector_ETH_YMHC.after_price * connector_YMHC_LYB.after_price)],
        [connector_ETH_YMHC.after_price, 1, 1 / connector_YMHC_LYB.after_price],
        [connector_ETH_YMHC.after_price * connector_YMHC_LYB.after_price, connector_YMHC_LYB.after_price, 1]
    ]

    return JsonResponse(ret, safe=False)
