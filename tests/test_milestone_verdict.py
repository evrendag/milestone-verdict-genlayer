import json
import base64


CONTRACT = "contracts/MilestoneVerdict.py"
CRITERIA = (
    "The delivery must contain a working REST endpoint, an OpenAPI document, "
    "and tests demonstrating both successful and invalid requests."
)
EVIDENCE_URL = "https://example.com/delivery-report"


def _create(contract, provider):
    from genlayer import Address

    provider_address = Address(base64.b64encode(provider).decode())
    return contract.create_milestone(
        provider_address, "Delivery API milestone", CRITERIA, 2
    )


def test_lifecycle_and_access_control(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    direct_vm.check_pickling = True
    direct_vm.sender = direct_alice
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    milestone_id = _create(contract, direct_bob)

    assert milestone_id == 0
    assert contract.get_milestone(0)["status"] == "OPEN"

    with direct_vm.prank(direct_charlie):
        with direct_vm.expect_revert("only the provider"):
            contract.submit_evidence(0, EVIDENCE_URL, "Unauthorized submission")

    with direct_vm.prank(direct_bob):
        contract.submit_evidence(
            0,
            EVIDENCE_URL,
            "The endpoint, OpenAPI document, and test report are linked.",
        )

    item = contract.get_milestone(0)
    assert item["status"] == "SUBMITTED"
    assert item["evidence_url"] == EVIDENCE_URL


def test_consensus_accepts_supported_delivery(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    _create(contract, direct_bob)

    with direct_vm.prank(direct_bob):
        contract.submit_evidence(0, EVIDENCE_URL, "Complete delivery attached.")

    proposal = {
        "decision": "ACCEPT",
        "score": 96,
        "payout_bps": 10000,
        "reason_codes": ["CRITERIA_MET"],
        "summary": "The endpoint, OpenAPI document, and positive/negative tests are present.",
    }
    evidence = (
        "Delivery report: endpoint deployed. OpenAPI document attached. "
        "Tests cover successful and invalid requests; all pass."
    )
    direct_vm.mock_web(r"example\.com/delivery-report", {"status": 200, "body": evidence})
    direct_vm.mock_llm(r"You are adjudicating", json.dumps(proposal))

    contract.adjudicate(0)
    item = contract.get_milestone(0)
    assert item["status"] == "ACCEPTED"
    assert item["payout_bps"] == 10000

    direct_vm.clear_mocks()
    direct_vm.mock_web(r"example\.com/delivery-report", {"status": 200, "body": evidence})
    direct_vm.mock_llm(r"independent validator", '{"accept": true}')
    assert direct_vm.run_validator() is True


def test_validator_rejects_unsupported_leader_verdict(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    direct_vm.sender = direct_alice
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    _create(contract, direct_bob)

    with direct_vm.prank(direct_bob):
        contract.submit_evidence(0, EVIDENCE_URL, "A partial draft is attached.")

    proposal = {
        "decision": "ACCEPT",
        "score": 95,
        "payout_bps": 10000,
        "reason_codes": ["CRITERIA_MET"],
        "summary": "Everything is complete.",
    }
    evidence = "Only a draft OpenAPI file exists. No endpoint or tests are available."
    direct_vm.mock_web(r"example\.com/delivery-report", {"status": 200, "body": evidence})
    direct_vm.mock_llm(r"You are adjudicating", json.dumps(proposal))
    contract.adjudicate(0)

    direct_vm.clear_mocks()
    direct_vm.mock_web(r"example\.com/delivery-report", {"status": 200, "body": evidence})
    direct_vm.mock_llm(r"independent validator", '{"accept": false}')
    assert direct_vm.run_validator() is False


def test_rejects_invalid_inputs(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.12")
    from genlayer import Address

    with direct_vm.expect_revert("criteria must contain"):
        contract.create_milestone(
            Address(base64.b64encode(direct_bob).decode()),
            "Too vague",
            "ship it",
            1,
        )

    milestone_id = _create(contract, direct_bob)
    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert("http or https"):
            contract.submit_evidence(milestone_id, "ipfs-only-value", "Proof")
