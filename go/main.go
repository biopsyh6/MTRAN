package main;

import (
	"fmt";
	"test_code/store";
)

func main(){

	myStore := store.NewStore();
	
	myStore = myStore.AddProduct("Ноутбук", 1200.50, 10);
	myStore = myStore.AddProduct("Мышь", 25.99, 50);
	myStore = myStore.AddProduct("Клавиатура", 45.75, 30);

	fmt.Println("Список товаров:")
	myStore.ListProducts()
	
	var test = "fjdksjkfs";

	myStore, success := myStore.BuyProduct("Ноутбук", 2);
	if success {
		fmt.Println("Покупка совершена!")
	} else {
		fmt.Println("Ошибка при покупке.")
	}
	
	
	myStore, success = myStore.BuyProduct("Мышь", 5); // fix

	fmt.Println("\nПосле покупки:")
	myStore.ListProducts()

	

	for i := 1; i < 10; i++ {
		fmt.Println(i * i)
	}
	
	var numbers = [10]int{1, -2, 3, -4, 5, -6, 7, 8, -9, 10};
	var sum = 0;

	for _, value := range numbers{
		if value < 0{
			continue
		}
		sum += value
	}
	fmt.Println("Sum:", sum)

	var numbers1 = [10]int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}; // fix
	var sum2 = 0;

	for _, value := range numbers1{
		if value > 4{
			break
		}
		sum2 += value
	}
	
	fmt.Println("Sum2:", sum2)
	fmt.Println("Factorial:", fact(5))


	initialUsers := [8]string{"Bob", "Alice", "Kate", "Sam", "Tom", "Paul", "Mike", "Robert"};
	users1 := initialUsers[2:6];
	users2 := initialUsers[:4];
	users3 := initialUsers[3:];

	fmt.Println(users1)
	fmt.Println(users2)
	fmt.Println(users3)

	var num = 1 + 1 * 2;
	fmt.Println(num);
}

func fact(x uint) uint{
	if x == 0{
		return 1
	}
	return x * fact(x - 1)
}