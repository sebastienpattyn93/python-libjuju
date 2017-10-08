import asyncio
import pytest
import uuid

from .. import base
from juju.controller import Controller
from juju.errors import JujuAPIError


@base.bootstrapped
@pytest.mark.asyncio
async def test_add_user(event_loop):
    async with base.CleanController() as controller:
        username = 'test{}'.format(uuid.uuid4())
        await controller.add_user(username)
        result = await controller.get_user(username)
        res_ser = result.serialize()['results'][0].serialize()
        assert res_ser['result'] is not None


@base.bootstrapped
@pytest.mark.asyncio
async def test_disable_enable_user(event_loop):
    async with base.CleanController() as controller:
        username = 'test-disable{}'.format(uuid.uuid4())
        await controller.add_user(username)
        await controller.disable_user(username)
        result = await controller.get_user(username)
        res_ser = result.serialize()['results'][0].serialize()
        assert res_ser['result'].serialize()['disabled'] is True
        await controller.enable_user(username)
        result = await controller.get_user(username)
        res_ser = result.serialize()['results'][0].serialize()
        assert res_ser['result'].serialize()['disabled'] is False


@base.bootstrapped
@pytest.mark.asyncio
async def test_change_user_password(event_loop):
    async with base.CleanController() as controller:
        username = 'test-password{}'.format(uuid.uuid4())
        await controller.add_user(username)
        await controller.change_user_password(username, 'password')
        try:
            new_controller = Controller()
            await new_controller.connect(
                controller.connection.endpoint, username, 'password')
            result = True
            await new_controller.disconnect()
        except JujuAPIError:
            result = False
        assert result is True


@base.bootstrapped
@pytest.mark.asyncio
async def test_grant(event_loop):
    async with base.CleanController() as controller:
        username = 'test-grant{}'.format(uuid.uuid4())
        await controller.add_user(username)
        await controller.grant(username, 'superuser')
        result = await controller.get_user(username)
        result = result.serialize()['results'][0].serialize()['result']\
            .serialize()
        assert result['access'] == 'superuser'
        await controller.grant(username, 'login')
        result = await controller.get_user(username)
        result = result.serialize()['results'][0].serialize()['result']\
            .serialize()
        assert result['access'] == 'login'


@base.bootstrapped
@pytest.mark.asyncio
async def test_list_models(event_loop):
    async with base.CleanController() as controller:
        async with base.CleanModel() as model:
            result = await controller.list_models()
            assert model.info.name in result


@base.bootstrapped
@pytest.mark.asyncio
async def test_get_model(event_loop):
    async with base.CleanController() as controller:
        by_name, by_uuid = None, None
        model_name = 'test-{}'.format(uuid.uuid4())
        model = await controller.add_model(model_name)
        model_uuid = model.info.uuid
        await model.disconnect()
        try:
            by_name = await controller.get_model(model_name)
            by_uuid = await controller.get_model(model_uuid)
            assert by_name.info.name == model_name
            assert by_name.info.uuid == model_uuid
            assert by_uuid.info.name == model_name
            assert by_uuid.info.uuid == model_uuid
        finally:
            if by_name:
                await by_name.disconnect()
            if by_uuid:
                await by_uuid.disconnect()
            await controller.destroy_model(model_name)


async def _wait_for_model_gone(controller, model_name):
    while model_name in await controller.list_models():
        await asyncio.sleep(0.5, loop=controller.loop)


@base.bootstrapped
@pytest.mark.asyncio
async def test_destroy_model_by_name(event_loop):
    async with base.CleanController() as controller:
        model_name = 'test-{}'.format(uuid.uuid4())
        model = await controller.add_model(model_name)
        await model.disconnect()
        await controller.destroy_model(model_name)
        await asyncio.wait_for(_wait_for_model_gone(controller,
                                                    model_name),
                               timeout=60)


@base.bootstrapped
@pytest.mark.asyncio
async def test_add_destroy_model_by_uuid(event_loop):
    async with base.CleanController() as controller:
        model_name = 'test-{}'.format(uuid.uuid4())
        model = await controller.add_model(model_name)
        model_uuid = model.info.uuid
        await model.disconnect()
        await controller.destroy_model(model_uuid)
        await asyncio.wait_for(_wait_for_model_gone(controller,
                                                    model_name),
                               timeout=60)
