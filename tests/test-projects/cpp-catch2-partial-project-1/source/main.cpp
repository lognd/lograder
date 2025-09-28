#define CATCH_CONFIG_MAIN
#include "catch_amalgamated.hpp"

TEST_CASE("Grouped sanity tests", "[sanity]") {
    SECTION("1?") {
        REQUIRE(1 == 1);
    }
    SECTION("2?") {
        REQUIRE(2 == 3);
    }
}