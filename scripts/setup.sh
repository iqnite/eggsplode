STEPS=5

echo "Eggsplode automatic setup v1.0"
echo "This script will install all dependencies and set up the environment for Eggsplode."
echo ""

read -p "Enter your Discord bot token (leave blank to skip): " YOUR_BOT_TOKEN
read -p "Enter your Discord test guild ID (leave blank to skip): " YOUR_TEST_GUILD_ID

echo "(1/$STEPS) Installing dependencies..."
sudo apt update -y
sudo apt install -y git python3 python3-pip python3-venv
echo ""

echo "(2/$STEPS) Cloning repository..."
git clone "https://github.com/iqnite/eggsplode.git"
cd eggsplode
echo ""

echo "(3/$STEPS) Setting up virtual environment..."
python3 -m venv .venv
python3 -m pip install --upgrade pip
source .venv/bin/activate
python3 -m pip install -r requirements.txt
echo ""

echo "(4/$STEPS) Setting up service..."
cp scripts/service-start.sh.example scripts/service-start.sh
sed -i "s|WORKING_DIRECTORY|$(pwd)|g" scripts/service-start.sh
chmod +x scripts/service-start.sh

cp scripts/eggsplode.service.example scripts/eggsplode.service
sed -i "s|CURRENT_USER|$USER|g" scripts/eggsplode.service
sed -i "s|WORKING_DIRECTORY|$(pwd)|g" scripts/eggsplode.service
chmod +x scripts/eggsplode.service
sudo cp scripts/eggsplode.service /etc/systemd/system/eggsplode.service
sudo systemctl daemon-reload
sudo systemctl enable eggsplode.service
echo ""

echo "(5/$STEPS) Configuring bot..."
if [ -n "$YOUR_BOT_TOKEN" ]; then
    cp .env.example .env
    sed -i "s|YOUR_BOT_TOKEN|$YOUR_BOT_TOKEN|g" .env
fi
if [ -n "$YOUR_TEST_GUILD_ID" ]; then
    cp resources/config.json.example resources/config.json
    sed -i "s|YOUR_TEST_GUILD_ID|$YOUR_TEST_GUILD_ID|g" resources/config.json
fi
echo ""

read -p "Setup complete! Start the bot now? (Y/n): " START_BOT
if [[ -z "$START_BOT" || "$START_BOT" =~ ^[Yy]$ ]]; then
    sudo systemctl start eggsplode.service
fi
