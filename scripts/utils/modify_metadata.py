from brownie import network
from helper_brownie import CHAINS
from scripts.utils.pinata import upload_file
from scripts.utils.helper import dump_to_json, load_from_json
from scripts.utils.config import PATH, PINATA, HASHLIPS
from scripts.collectible.config import (
    COLLECTION,
    SPREADSHEET,
    SINGLE_EDITION_COLLECTION,
)
from scripts.utils.spreadsheet import _get_nft_spreadsheet_data


def main():
    modify_metadata()


def modify_metadata(_token_id: int = None):

    """
    Modify metadata that is generated by hashlips engine.
    Insert additional data from spreadsheet.
    Upload image and metadata to IPFS/Pinata if enabled.
    Return token_uri.
    """

    token_id = _token_id

    """
    @dev Add to image path a dinamic endpoint that is based on the random file name.
    """
    image_path = (
        PATH["images"] + f"/{token_id}.png"
        if HASHLIPS["enabled"] or not SINGLE_EDITION_COLLECTION["enabled"]
        else PATH["images"] + f"/{SINGLE_EDITION_COLLECTION['file_name']}"
    )

    metadata_path = PATH["token_metadata"] + f"/{token_id}.json"
    token_uri_path = PATH["token_URIs"] + f"/{token_id}.json"

    metadata = load_from_json(metadata_path)
    token_uri = load_from_json(token_uri_path)

    print(f"Modifying metadata of token ID: {token_id} ...")

    # Delete unnecessary keys made by hashlips engine.
    if HASHLIPS["enabled"]:
        try:
            del metadata["dna"]
            del metadata["date"]
            del metadata["edition"]
            del metadata["compiler"]
        except KeyError:
            print(f"---KeyError occured. Working further on tokenId {token_id}---")

    # Inserting spreadsheet data to the metadata.
    if SPREADSHEET["enabled"]:
        ss_data = _get_nft_spreadsheet_data(PATH["spreadsheet"], token_id)

        metadata["name"] = ss_data["NAME"]
        metadata["description"] = ss_data["DESCRIPTION"]
        metadata["creator"] = ss_data["CREATOR"]
        metadata["artist"] = ss_data["ARTIST"]

        if (
            HASHLIPS["enabled"]
            and not HASHLIPS["include_generated_metadata_attributes"]
        ):
            metadata["attributes"] = []

        for key, value in ss_data.items():
            if key in SPREADSHEET["trait_types"]:
                for v in value:  # loop through value list
                    metadata["attributes"].append(
                        {"trait_type": key, "value": v.capitalize()}
                    )
    else:
        if SINGLE_EDITION_COLLECTION["enabled"]:
            metadata["name"] = COLLECTION["artwork"]["name"]
            metadata["description"] = COLLECTION["artwork"]["description"]
        else:
            metadata["name"] = COLLECTION["artwork"]["name"] + f" #{token_id}"
            metadata["description"] = COLLECTION["artwork"]["description"]

        metadata["creator"] = COLLECTION["artwork"]["creator"]
        metadata["artist"] = COLLECTION["artwork"]["artist"]

    # Inserting external link to the metadata.
    if COLLECTION["external_link"]["enabled"]:
        metadata["external_link"] = _get_nft_external_link(token_id)

    # Inserting additional key/value to the metadata.
    if COLLECTION["artwork"]["additional_metadata"]["enabled"]:
        for k, v in COLLECTION["artwork"]["additional_metadata"]["data"].items():
            metadata[k] = v

    if PINATA["enabled"] and network.show_active() not in CHAINS["local"]:

        # metadata["image"] = upload_to_ipfs(image_path)
        metadata["image"] = upload_file(image_path)
        dump_to_json(metadata, metadata_path)

        # token_uri[str(token_id)] = upload_to_ipfs(metadata_path)
        token_uri[str(token_id)] = upload_file(metadata_path)
        dump_to_json(token_uri, token_uri_path)

    else:

        metadata["image"] = f"ipfs://YourImageUri/{token_id}.png"
        dump_to_json(metadata, metadata_path)

        token_uri[str(token_id)] = f"ipfs://YourTokenUri/{token_id}.json"
        dump_to_json(token_uri, token_uri_path)

    print(f"Finished modifying metadata of token ID: {token_id}")

    return token_uri[str(token_id)]


def _get_nft_external_link(_token_id):
    if COLLECTION["external_link"]["include_token_id"]:
        return COLLECTION["external_link"]["url"] + str(_token_id)
    return COLLECTION["external_link"]["url"]
