import os
from pathlib import Path
from typing import Literal, Tuple

import dotenv
from smart_contracts.community import contract as community_contract
from smart_contracts.nfts import contract as nft_contract

AurallyContract = Literal["NFT", "Community"]


def build_contract(contract_name: str, contract: AurallyContract) -> Tuple[str, str]:
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
            build = nft_contract.app.build()
            build.export(artifacts_dir)
            return (build.approval_program, build.clear_program)
        case "Community":
            build = community_contract.app.build()
            build.export(artifacts_dir)
            return (build.approval_program, build.clear_program)
