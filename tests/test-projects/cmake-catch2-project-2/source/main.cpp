#define CATCH_CONFIG_MAIN
#include <catch2/catch_test_macros.hpp>
#include "two.hpp"

TEST_CASE("Grouped sanity tests", "[sanity]") {
	REQUIRE(make_two() == 2);
}