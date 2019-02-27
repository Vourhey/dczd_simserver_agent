{ stdenv
, mkRosPackage
, robonomics_comm
}:

mkRosPackage rec {
  name = "${pname}-${version}";
  pname = "dczd_simserver_agent";
  version = "master";

  src = ./.;

  propagatedBuildInputs = [ robonomics_comm ];

  meta = with stdenv.lib; {
    description = "DCZD Simserver Agent";
    homepage = http://github.com/airalab/dczd_simserver_agent;
    license = licenses.bsd3;
    maintainers = with maintainers; [ vourhey ];
  };
}
