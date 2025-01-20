echo "CHAUDIERE: 	$(raspi-gpio get | grep 21)"
echo "PLANCHER: 	$(raspi-gpio get | grep 16)"
echo "ECS:		$(raspi-gpio get | grep 20)"
echo "Remote-gpio16	$(raspi-gpio get | grep 16)"
