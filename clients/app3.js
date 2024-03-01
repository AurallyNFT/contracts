"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var algosdk_1 = require("algosdk");
var fs_1 = require("fs");
var path_1 = require("path");
var readline_1 = require("readline");
var algokit = require("@algorandfoundation/algokit-utils");
var approvalFilePath = (0, path_1.join)(__dirname, '../../aurally_contract/contract/smart_contracts/artifacts/Aurally_NFT/approval.teal');
var clearFilePath = (0, path_1.join)(__dirname, '../../aurally_contract/contract/smart_contracts/artifacts/Aurally_NFT/clear.teal');
try {
    var client_1 = algokit.getAlgoClient({
        port: "",
        server: "https://mainnet-api.algonode.cloud",
        token: ""
    });
    var approvalProgram_1 = (0, fs_1.readFileSync)(approvalFilePath);
    var clearProgram_1 = (0, fs_1.readFileSync)(clearFilePath);
    console.log("Approval Size:", "".concat(approvalProgram_1.byteLength, " bytes"));
    console.log("Clear Size", "".concat(clearProgram_1.byteLength, " bytes"));
    console.log("Total Size", "".concat(approvalProgram_1.byteLength + clearProgram_1.byteLength, " bytes"));
    var reader = (0, readline_1.createInterface)({
        input: process.stdin,
        output: process.stdout
    });
    reader.question("Enter mnemonics\n", function (input) {
        var privateKey = algosdk_1.default.mnemonicToSecretKey(input);
        client_1.getTransactionParams().do().then(function (params) {
            var appUpdateTxn = algosdk_1.default.makeApplicationUpdateTxnFromObject({
                from: "6NN46NIZ3SN5B6LPQTEXFHW6A3J562IHTCKUINYHUYXEHSDAGFHAZ7A3DM",
                appIndex: 1581977710,
                approvalProgram: new Uint8Array(approvalProgram_1.buffer, approvalProgram_1.byteOffset, approvalProgram_1.byteLength),
                clearProgram: new Uint8Array(clearProgram_1.buffer, clearProgram_1.byteOffset, clearProgram_1.byteLength),
                suggestedParams: params,
            });
            client_1.sendRawTransaction(appUpdateTxn.signTxn(privateKey.sk)).do().then(function () {
                algosdk_1.default.waitForConfirmation(client_1, appUpdateTxn.txID().toString(), 3).then(function (res) { return console.log(res); });
            });
        });
    });
}
catch (err) {
    console.log("Error reading the files: ".concat(err));
}
