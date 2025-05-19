require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$PH_ID = $in{'PH_ID'};

$WHICHDB    = $in{'WHICHDB'};
$PH_ID      = $in{'PH_ID'};
$USER       = $in{'USER'};
##$WHICHDB = 'Webinar' if($USER == 1489);
$Agg_String = $in{'Agg_String'};

my @cat;
my @months;
my @payers;
my @prevmonths;
my @colors = ( 
            '\#BCD2E8', '\#91BAD6', '\#73A5C6', '\#528AAE', '\#2E5984', '\#1E3F66',
            '\#78CFDE', '\#6AB6D9', '\#71A6D1', '\#6893C0', '\#5B80AF', '\#44648E' 
          );

my %payers;

($WHICHDB)  = &StripJunk($WHICHDB);

&readsetCookies;
&readPharmacies;

print "Set-Cookie:AreteUser=$Pharmacy_Arete{$PH_ID}; path=/; domain=$cookie_server;\n"  if($Pharmacy_Arete{$PH_ID});
print "Set-Cookie:Agg_String=$Agg_String; path=/; domain=$cookie_server;\n"  if ( $PH_ID  eq 'Aggregated');

# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January

#______________________________________________________________________________

if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    &ReconRxAggregatedHeaderBlock_New;
  }
  else {
    if ($USER != 66) {
      &ReconRxHeaderBlock;
	  #&ReconRxHeaderBlockNew;
    }
    else {
      &ReconRxHeaderBlock;
      #&ReconRxHeaderBlockNew;
    }
  }
} else {
   &ReconRxGotoNewLogin;
   exit(0);
}

#______________________________________________________________________________


### Log pharmacy login

if ( $TYPE =~ /^\s*$/ ) {
   if ( $USER !~ m/[^0-9.]/ && $USER > 0 && $OWNER !~ /pharmassess/i) {
      $Pharmacy_Name = $Pharmacy_Names{$USER};
      &logActivity($Pharmacy_Name, "Logged in to ReconRx", $USER);
   } else {
      if ( $USER eq $OWNER ) {
         &logActivity($RUSER, "SuperUser Logged in to ReconRx", NULL);
      }
   }
}

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

if ($PH_ID) {
  if ( $PH_ID  eq 'Aggregated') {
    $PH_ID = $Agg_String;
  }
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23") {
	$DBNAME = "Webinar";
  }
  #print "PH_ID: $PH_ID  DBNAME: $DBNAME\n";
  &displayPharmacyRight($PH_ID);
  &get_cats;
  &get_payers;
  &build_data;
  &build_barchart_report;
  &build_line_report;
}

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayPharmacyRight {
  my ($PH_ID) = @_;
  print qq#<!-- displayPharmacyRight -->\n#;

  $ntitle = "DIR Fee Report Monthly";
  print qq#<h1 class="page_title">$ntitle</h1>\n
  <script src="https://code.highcharts.com/highcharts.js"></script>
  <script src="https://blacklabel.github.io/grouped_categories/grouped-categories.js"></script>
  #;
  ##<script src="https://code.highcharts.com/modules/exporting.js"></script>

  print "sub displayPharmacyRight: Exit.<br>\n" if ($debug);
}

sub get_cats {
  my $sql = " SELECT concat(Year(CURRENT_DATE - INTERVAL 6 MONTH),lpad(MONTH(CURRENT_DATE - INTERVAL 6 MONTH),2,0))
               UNION
              SELECT concat(Year(CURRENT_DATE - INTERVAL 5 MONTH),lpad(MONTH(CURRENT_DATE - INTERVAL 5 MONTH),2,0))
               UNION
	      SELECT concat(Year(CURRENT_DATE - INTERVAL 4 MONTH),lpad(MONTH(CURRENT_DATE - INTERVAL 4 MONTH),2,0))
	       UNION
	      SELECT concat(Year(CURRENT_DATE - INTERVAL 3 MONTH),lpad(MONTH(CURRENT_DATE - INTERVAL 3 MONTH),2,0))
	       UNION
	      SELECT concat(Year(CURRENT_DATE - INTERVAL 2 MONTH),lpad(MONTH(CURRENT_DATE - INTERVAL 2 MONTH),2,0))
	       UNION
	      SELECT concat(Year(CURRENT_DATE - INTERVAL 1 MONTH),lpad(MONTH(CURRENT_DATE - INTERVAL 1 MONTH),2,0))
           ";

  $sthg = $dbx->prepare($sql);
  $sthg->execute();
  my $numofrows = $sthg->rows;
  $categories = '';

  if ($numofrows > 0) {
    while (($mnth) = $sthg->fetchrow_array()) {
      $prevmnth = $mnth - 100;
      $m = substr($mnth,4,2) + 0;
      $m = $FMONTHS{$m};
      push(@cat,"'$m',");
      push(@months,$mnth);
      push(@prevmonths,$prevmnth);
    }
  }
}

sub get_payers {

  my $currdte = shift;
  my $prevdte = currdte - 100;
  my $months = join(',', @months);
  my $prevmonths = join(',', @prevmonths);

  my $sql = "SELECT  tpp_id, third_party_payer_name 
               from $DBNAME.dir_monthly  a
               JOIN officedb.third_party_payers b on a.tpp_id = b.third_party_payer_id
              WHERE Pharmacy_ID IN ($PH_ID) 
                AND yearmo IN ($months, $prevmonths)
              GROUP BY tpp_ID
            ";
  $sthp = $dbx->prepare($sql);
  $sthp->execute();
  my $numofrows = $sthp->rows;

  if ($numofrows > 0) {
    while (($tppid,$tppname) = $sthp->fetchrow_array()) {
      push(@payers,$tppid);
      $payers{$tppid} = "$tppname";
    }
  }
         	
  
}

sub build_data {

my $mnth;

  foreach $mnth (@months) {
    foreach $payer (@payers) {
      $amt = 0;
      my $sql = " SELECT yearmo, third_party_payer_name, sum(Total_DIR_PLB)  
                    FROM $DBNAME.dir_monthly  a
                    JOIN officedb.third_party_payers b on a.tpp_id = b.third_party_payer_id
                   WHERE Pharmacy_ID IN ($PH_ID) 
                     AND yearmo = $mnth 
                     AND tpp_id = $payer
                ";
      $sthg = $dbx->prepare($sql);
      my $numofrows = $sthg->execute();

      if ($numofrows > 0) {
        while (my @row = $sthg->fetchrow_array()) {
          my ($yrmo, $tpp, $amt) =  @row;
          $amt = sprintf("%.2f",$amt);
          $tpp = $payers{$payer} if(!$tpp);
          $curseries{$tpp}  .= "$amt,";
        }
      }
      $sthg->finish();
    }
  }

  foreach $mnth (@prevmonths) {
    foreach $payer (@payers) {
      my $sql = " SELECT yearmo, third_party_payer_name, sum(Total_DIR_PLB)
                    FROM $DBNAME.dir_monthly  a
                    JOIN officedb.third_party_payers b on a.tpp_id = b.third_party_payer_id
                   WHERE Pharmacy_ID IN ($PH_ID) 
                     AND yearmo = $mnth 
                     AND tpp_id = $payer
                ";

      $sthg = $dbx->prepare($sql);
      $sthg->execute();
      my $numofrows = $sthg->rows;
      $amt = 0;

      if ($numofrows > 0) {
        while (my @row = $sthg->fetchrow_array()) {
          my ($yrmo, $tpp, $amt) =  @row;
          $amt = sprintf("%.2f",$amt);
          $tpp = $payers{$payer} if(!$tpp);
          $prevseries{$tpp}  .= "$amt,";
        }
      }
      $sthg->finish();
    }
  }
}

sub build_barchart_report {

  print qq#
    <script>
    \$(function () {
      \$('\#container1').highcharts({
        chart: {
          type: 'column'
        },
        title: {
	  style: { color: '\#133562', fontWeight: 'bold', fontSize: '18px', fontFamily: 'Trebuchet MS' },
          text: 'DIR Fees (Year to Year Comparison)'
        },
        subtitle: {
	  style: { color: '\#133562', fontSize: '16px', fontFamily: 'Trebuchet MS' },
          text: 'Where data is available'
        },
		credits: {
			enabled: false
		},
        xAxis: {
          categories: [ @cat ],
          labels: {
            format: '<div style="text-align:center;"> Prev Year&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Curr Year&nbsp; <br /><br /><h3 style= "padding:0px; margin:0px;">{value}</h3></div>',
            useHTML: true
          },
        },
        yAxis: {
          min: 0,
          title: {
            text: 'DIR Fees'
          }
        },
        tooltip: {
           format: '<b>{key}</b><br/>{series.name}: \${y}<br/>' +
            'Total: \${point.stackTotal}'
        },
        plotOptions: {
          column: {
            stacking: 'normal'
          }
        },
       #;

       $sercount = 0;
        foreach $dirtpp (keys %prevseries) {
          $thcolor = $colors[$sercount];
          $dataset = $prevseries{$dirtpp};

          if($sercount) {
            print  qq#
              ,
            #;
          }
          else {
            print  qq#
              series: [
            #;
          }
          print  qq#
            { name: '${dirtpp}(PY)',
              data: [$dataset],
              color:'$thcolor',
              stack: 'Previous'
            }
          #;
          $sercount++;
        }

        foreach $dirtpp (keys %curseries) {
          $thcolor = $colors[$sercount];
          $dataset = $curseries{$dirtpp};

          if($sercount) {
            print  qq#
              ,
            #;
          }
          else {
            print  qq#
              series: [
            #;
          }

          print  qq#
            { name: '$dirtpp',
              data: [$dataset],
              color: '$thcolor',
              stack: 'Current',
              tooltip: {
              valueSuffix: 'Current'
              }
            }
          #;
          $sercount++;
        }
        print  qq#
          ]});
      });
    </script>
  #;
  print  qq#
    <hr style="margin: 18px 0px; color: \#5FC8ED;" />
    <div id="container1" style="min-width: 200px; height: 400px; margin: 0 auto;"></div>
    <hr style="margin: 18px 0px; color: \#5FC8ED;" />
  #;
}

sub build_line_report {

  print qq#
  <script>
    \$(function () {
      \$('\#container2').highcharts({
        chart: {
          type: 'spline'
        },
        title: {
	  style: { color: '\#133562', fontWeight: 'bold', fontSize: '18px', fontFamily: 'Trebuchet MS' },
           text: 'DIR Fees (Current Year)'
        },
        subtitle: {
	  style: { color: '\#133562', fontSize: '16px', fontFamily: 'Trebuchet MS' },
           text: 'Where data is available'
        },
	credits: {
	  enabled: false
	},
        xAxis: {
          categories: [ @cat ]
        },
        yAxis: {
          min: 0,
          title: {
           text: 'DIR Fees'
          }
        },
        tooltip: {
           format: '<b>{key}</b><br/>{series.name}: \${y}' 
        },
        plotOptions: {
          column: {
            stacking: 'normal'
          }
        },
      #;

        $sercount = 0;
        foreach $dirtpp (keys %curseries) {
          $thcolor = $colors[$sercount];
          $dataset = $curseries{$dirtpp};

          if($sercount) {
            print  qq#
              ,
            #;
          }
          else {
            print  qq#
              series: [
            #;
          }
          print  qq#
            { name: '$dirtpp',
              data: [$dataset ],
              color: '$thcolor',
              stack: 'Current',
              tooltip: {
                valueSuffix: 'Current'
              }
            }
          #;
          $sercount++;
        }
      print  qq#
        ]});
      });
  </script>
        #;
  print  qq#
    <div id="container2" style="min-width: 200px; height: 400px; margin: 0 auto;"></div>
    <hr style="margin: 18px 0px; color: \#5FC8ED;" />
  #;
}
   
