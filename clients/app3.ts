import algosdk from "algosdk";
import { readFileSync } from "fs"
import { join } from 'path';
import { createInterface } from "readline"
import * as algokit from '@algorandfoundation/algokit-utils'

const approvalFilePath = join(__dirname, '../../aurally_contract/contract/smart_contracts/artifacts/Aurally_NFT/approval.teal');
const clearFilePath = join(__dirname, '../../aurally_contract/contract/smart_contracts/artifacts/Aurally_NFT/clear.teal');
try {
  const client = algokit.getAlgoClient({
    port: "",
    server: "https://mainnet-api.algonode.cloud",
    token: ""
  })
  const approvalProgram = readFileSync(approvalFilePath)
  const clearProgram = readFileSync(clearFilePath)
  console.log("Approval Size:", `${approvalProgram.byteLength} bytes`)
  console.log("Clear Size", `${clearProgram.byteLength} bytes`)
  console.log("Total Size", `${approvalProgram.byteLength + clearProgram.byteLength} bytes`)
  const reader = createInterface({
    input: process.stdin,
    output: process.stdout
  })
  reader.question("Enter mnemonics\n", (input) => {
    const privateKey = algosdk.mnemonicToSecretKey(input)
    client.getTransactionParams().do().then(params => {
      const appUpdateTxn = algosdk.makeApplicationUpdateTxnFromObject({
        from: "6NN46NIZ3SN5B6LPQTEXFHW6A3J562IHTCKUINYHUYXEHSDAGFHAZ7A3DM",
        appIndex: 1581977710,
        approvalProgram: new Uint8Array(approvalProgram.buffer, approvalProgram.byteOffset, approvalProgram.byteLength),
        clearProgram: new Uint8Array(clearProgram.buffer, clearProgram.byteOffset, clearProgram.byteLength),
        suggestedParams: params,
      })
      client.sendRawTransaction(appUpdateTxn.signTxn(privateKey.sk)).do().then(() => {
        algosdk.waitForConfirmation(client, appUpdateTxn.txID().toString(), 3).then(res => console.log(res))
      })
    })
  })
} catch (err) {
  console.log(`Error reading the files: ${err}`)
}
