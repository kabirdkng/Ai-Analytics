const hre = require("hardhat");

async function main() {
  console.log("Deploying AnalyticsRegistry contract...");

  const AnalyticsRegistry = await hre.ethers.getContractFactory("AnalyticsRegistry");
  const registry = await AnalyticsRegistry.deploy();

  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log(`AnalyticsRegistry deployed to: ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
