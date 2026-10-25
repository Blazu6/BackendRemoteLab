import pytest
from lab.models import Machine, PDU, PDUOutletMapping, Document, LaboratorySession
from django.contrib.auth.models import Group, User
from django.contrib.auth import get_user_model

"""
Test cases:
1. First create group lab_wtorek and user jan. Add jan to lab_wtorek group. Add one test machine. Assign lab_wtorek to allowed_group.
Check if the jan has acces to the machine
2. Add adam but he is not in the group and then we check if he has acces to the machine
"""
@pytest.mark.django_db
def test_db_case():
    #1.
    test_group = Group.objects.create(name="lab_wtorek")
    test_user = User.objects.create_user(username='jan', password='test')
    test_user.groups.add(test_group)
    test_machine = Machine.objects.create(
	    name="Router 1",
	    hostname="192.168.1.1",
	    port=22,
	    protocol=Machine.Protocol.SSH,
	    password="test",
	)
    test_machine.allowed_groups.add(test_group)
    allowed_machines = Machine.objects.filter(allowed_groups__in=test_user.groups.all())
    assert test_machine in allowed_machines
    #2.
    test_user_2 = User.objects.create(username="adam", password="test")
    adam_machines = Machine.objects.filter(allowed_groups__in=test_user_2.groups.all())
    assert test_machine not in adam_machines

