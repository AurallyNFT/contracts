import os
from pathlib import Path
from typing import Literal
import dotenv

from smart_contracts.nfts import contract as nft_contract
from smart_contracts.community import contract as community_contract


AurallyContract = Literal["NFT", "Community"]


def build_contract(contract_name: str, contract: AurallyContract):
    dotenv.load_dotenv()
    artifacts_dir = (
        Path(__file__)
        .parent.parent.joinpath("smart_contracts")
        .joinpath("artifacts")
        .joinpath(contract_name)
    )
    if not artifacts_dir.is_dir():
        os.makedirs(artifacts_dir, exist_ok=True)
    match contract:
        case "NFT":
            nft_contract.app.build().export(artifacts_dir)
        case "Community":
            community_contract.app.build().export(artifacts_dir)
