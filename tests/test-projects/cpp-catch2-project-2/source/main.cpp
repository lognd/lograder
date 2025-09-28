#define CATCH_CONFIG_MAIN
#include "catch_amalgamated.hpp"
#include "two.hpp"

TEST_CASE("Grouped sanity tests", "[sanity]") {
	REQUIRE(make_two() == 2);
}