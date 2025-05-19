require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$LDATEADDED = $in{'LDATEADDED'};

my $submitvalue = "SAVE";

#______________________________________________________________________________

&readsetCookies;

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
#______________________________________________________________________________

&readPharmacies;

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
   
DBI->trace(1) if ($dbitrace);

&readThirdPartyPayers;

&read_tpp_problems;

$ntitle = "Reconciling Third Party Payers";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayWebPage;

#______________________________________________________________________________

&MyReconRxTrailer;

$dbx->disconnect;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;

  ($PROG = $prog) =~ s/_/ /g;
  
  print qq#<br /><table class="main">\n#;
  print qq#<tr valign=top><td class="multi_table">\n#;
  
  print qq#<table class="secondary">\n#;
  print qq#<tr><th class="align_left">Third Party Payer</th>#;
  print qq#<th class="align_center">BIN</th>#;
  print qq#<th class="align_left">**Payment Cycle</th>#;
  print qq#<th class="align_center">ACH<br>Forms</th>#;
  print qq#</tr>\n#;
  
  $displaycount = 0;
	 
  #FROM SWITCH
  $sql = "
  SELECT a.tpp_id, b.Third_Party_Payer_Name, b.BIN, b.Payment_Cycle, b.Website, c.location
  FROM reconrxdb.tpp_list a
  LEFT JOIN officedb.third_party_payers b
  ON a.tpp_id = b.Third_Party_Payer_ID 
  LEFT JOIN reconrxdb.form_mst c
  ON (a.tpp_id = c.tpp_id AND c.Active = 1)
  WHERE Third_Party_Payer_Name IS NOT NULL
  GROUP BY a.tpp_id
  ORDER BY b.Third_Party_Payer_Name
  ";

  ($sqlout = $sql) =~ s/\n/<br>\n/g;
	 
  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  while (my @row = $sthrp->fetchrow_array()) {

    my ($R_TPP_PRI, $Third_Party_Payer_Name, $BIN, $Payment_Cycle, $Website, $location) = @row;

    if ( $BIN > 999990 ) {
       next;
    } 

    next if ( $TPP_Reconciles{$R_TPP_PRI} =~ /^No$/i );

    $bgcolor = "green";
	
	if ($Website =~ /^\s*$/) {
	  $Website = '';
	} elsif ($Website !~ /^HTTP/i) {
	  $Website = "http://" . $Website;
	}

    if ($Problem_BIN{$BIN} !~ /^\s*$/) {
      $bgcolor = $Problem_Status{$BIN};
    }
	
	  #Column: Third Party Payer
    print qq#<tr><td class="$bgcolor">#;
    if ($Problem_Problem{$BIN} !~ /^\s*$/) {
      print qq#<a href='\#' onclick='overlay$BIN()'><img src="/images/question.png" /></a> #;

      print qq#			 
      <div id="bin$BIN" class="overlay">
        <div>
          <p class="$bgcolor"><strong>$Third_Party_Payer_Name</strong></p>
          <p>$Problem_Problem{$BIN}</p>
          <p><a href='\#' onclick='overlay$BIN()'><strong>CLOSE</strong></a></p>
        </div>
      </div>
      #;

      print qq#
      <script>
        function overlay$BIN() {
          el = document.getElementById("bin$BIN");
          el.style.visibility = (el.style.visibility == "visible") ? "hidden" : "visible";
        }
      </script>
      #;
			 
    }
	
    if ( $Website !~ /^\s*$/i ) {
      print qq#<a href="$Website" target="_blank">$Third_Party_Payer_Name</a>#;
    } else {
      print qq#$Third_Party_Payer_Name#;
    }
    print qq#</td>#;

	  #Column: BIN
    print qq#<td class="align_center $bgcolor" nowrap>$BIN</td>\n#;
	
	  #Column: Payment Cycle
    print qq#<td class="align_left $bgcolor">$Payment_Cycle</td>\n#;

	  #Column: ACH Form
    print qq#<td class="align_center $bgcolor" valign=middle>#;

    if ( $location =~ /_/ ) {
      print qq#<a href="../$location"><img src="/images/download.png" width="12" height="12" ></a> $nbsp#;
      $printed++;
    } 
    else {
      print qq#N/A $nbsp#;
    }
    print qq#</td>#;
		   
    print qq#</tr>\n#;
		   
    $displaycount++;
	
  }
  $sthrp->finish;
	 
  if ( $displaycount ) {
    print qq#<tr><td colspan=4>**The above listed payment cycles were provided directly from the third party payers and apply to all of their plans (unless otherwise specified).</td></tr>\n#;
    print qq#<tr><td colspan=4><br>$displaycount Payers listed</td></tr>\n#;
  } else {
    print qq#<tr><td colspan=4>No Third Party Payers</td></tr>\n#;
  }
  
  print qq#</table>\n#;

  print qq#</td><td class="multi_table">\n#;
   
  print "$nbsp $nbsp $nbsp<br>\n";

  print qq#</td><td class="multi_table">\n#;
   
  print qq#<table class="secondary">\n#;
  print qq#<tr align=top><th colspan=2 class="align_center">Key</th></tr>\n#;
  print qq#<tr align=top><td class="green"  height="50"><strong>Green</strong> </td> <td class="green" >No Payment Issues</td></tr>\n#;
  print qq#<tr align=top><td class="yellow" height="50"><strong>Yellow</strong></td> <td class="yellow">Slow Payment -<br>Remit Issues</td></tr>\n#;
  print qq#<tr align=top><td class="red"    height="50"><strong>Red</strong>   </td> <td class="red"   >Major Payment Issues</td></tr>\n#;
  print qq#</table>\n#;
	 
  print qq#</td></tr>\n#;
  
  print qq#</table>\n#;
}

#______________________________________________________________________________

sub read_tpp_problems {

  my $dbb = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

  DBI->trace(1) if ($dbitrace);
  
  my $DBNAME = "reconrxdb";
  my $TABLE  = "tpp_problems";

  my $sql = "
  SELECT LPAD(BIN, 6, 0) as BIN, Status, Problem 
  FROM $DBNAME.$TABLE
  ";

  my $sthx  = $dbb->prepare("$sql");
  $sthx->execute;

  my $NumOfRows = $sthx->rows;

  while ( my @row = $sthx->fetchrow_array() ) {

     my ($BIN, $Status, $Problem) = @row;

     $Problem_BINs{$BIN}++;
     $Problem_BIN{$BIN}      = $BIN;
     $Problem_Status{$BIN}   = $Status;
     $Problem_Problem{$BIN} = $Problem;

  }
  $sthx->finish;
  $dbb->disconnect;
}

#______________________________________________________________________________
