## Add SuperUser
# Purpose: To add a SuperUser without requiring Devs
# Date last updated: 15 December 2022
# Version: 1.3.1
# Maintainer: Katherine Hays
##

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use Excel::Writer::XLSX;

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

my $testing = 0;

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;
  
my $tbl_weblogin = 'weblogin';
my $tbl_webdtl   = 'weblogin_dtl';
my $db_office    = 'officedb';

foreach $key (sort keys %in) {
  $$key = $in{$key};
}

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;
   exit(0);
}

#______________________________________________________________________________

&hasAccess($USER);

if ( $ReconRx_Add_SuperUser !~ /^Yes/i ) {
   print qq#<p class="yellow"><font size=+1><strong>\n#;
   print qq#$prog<br><br>\n#;
   print qq#<i>You do not have access to this page.</i>\n#;
   print qq#</strong></font>\n#;
   print qq#</p><br>\n#;
   print qq#<a href="javascript:history.go(-1)"> Go Back </a><br><br>\n#;

   &trailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong><br>\n#;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;    # reported as "years since 1900".
$month += 1;    # reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);

$long_time  = sprintf("%04d%02d%02d%02d%02d", $year, $month, $day, $hour, $min);

($in_TPP_ID, $in_TPP_BIN, $in_TPP_NAME) = split("##", $filter_in, 3);
 
my $dbi_connection = DBI->connect("DBI:mysql:$db_office:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);


&displayPage;

$dbi_connection->disconnect;

exit(0);

#______________________________________________________________________________
 
sub displayPage {
  
  # -------------------------------------------------------------------------------- #
  
  print "in_TPP_ID: $in_TPP_ID<br>\n" if ($debug);

  my ($TPP_ID, $TPP_BIN, $TPP_NAME);
  
  # -------------------------------------------------------------------------------- #
 
  print qq~
  
  <link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />
  <script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
  <script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>

  
  <style>
  \@import url('//maxcdn.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.min.css');

  .info-msg,
  .success-msg,
  .warning-msg,
  .error-msg {
    margin: 10px 0;
    padding: 10px;
    border-radius: 3px 3px 3px 3px;
  }
  .success-msg {
    color: #270;
    background-color: #DFF2BF;
  }
  .error-msg {
    color: #D8000C;
    background-color: #FFBABA;
  }
  .warning-msg {
   color: #9F6000;
   background-color: #FEEFB3;
  }
  </style>
  ~;

  print qq#<form method="POST" autocomplete="off">#;
  print qq~
  <br>
  <table class="noborders">
    <tr>
      <td><label>Username:* </td>
      <td> <input type="text" name="username" value="$username"></input> </td>
      </label>
    </tr>
    <tr>
      <td> <label>Password:* </td>
      <td> <input type="text" name="password" value="$password"></input> </td>
      <td> <span style="font-size:9pt;"><em>PW Requirements: 8 characters, at least one letter, at least one number.</em></span> </td>
      </label>
    </tr>
    <tr>
      <td><label>NCPDPs:*</td>
      <td><input type="text" name="ncpdp" value="$ncpdp"></input></td>
      <td> <span style="font-size:9pt;"><em>(Comma-Seperated)</em></span> </td>
      </label>
    </tr>
  </table>

  <br>
  <table class="noborders">
    <tr>
      <td>Programs:*</td>
    <td><label>ReconRx </td>
      <td> <input type="checkbox" name="recon_rx" value="1"~; $recon_rx ? print 'checked' : ''; print qq ~></input>
      </label>
    </td>
    </tr>
    <tr>
      <td></td>
      <td> <label>RBS </td>
        <td> <input type="checkbox" name="rbs" value="1"~; $rbs ? print 'checked' : ''; print qq ~></input>
        </label>
      </td>
    </tr>
    <tr>
      <td></td>
      <td><label>Cred </td>
        <td> <input type="checkbox" name="cred" value="1"~; $cred ? print 'checked' : ''; print qq ~ ></input>
        </label>
      </td>
    </tr>
    </table>
  
  <br>
  <label>Aggregated
    <input type="checkbox" name="aggregated" value="1"~; $aggregated ? print 'checked' : ''; print qq ~></input>
  </label><br>~;

  print qq#<p><input class="button-form" type="submit" value="Add SuperUser"></p>#;
  print qq#</form>#;
  
  print "<\hr>\n";
  
  my @program_list;
  
  if ($recon_rx) {
    push(@program_list, 'ReconRx');
  }
  if ($rbs) {
    push(@program_list, 'RBS');
  }
  if ($cred) {
    push(@program_list, 'Cred');
  }
  
  my $programs = join(':', @program_list);
  print "PROGRAMS: $programs" if $testing;
  
  if ($ncpdp && $username && $password && $programs) {
    
    my $username_quote = $dbi_connection->quote($username);
    my $password_quote = $dbi_connection->quote($password);
	$ncpdp =~ s/\s//g;
    my $warning_ncpdp = $ncpdp !~ /[0-9]{7}(\s|),(\s|)[0-9]{7}/ && $aggregated ? 1 : 0;
    my $agg_binary = $aggregated ? ($warning_ncpdp ? '0' : '1') : '0';
    
    my $existing_login = qq~ SELECT login
      FROM $db_office.$tbl_weblogin
      WHERE login = $username_quote
      LIMIT 1;~;
    my $prep_existing = $dbi_connection->prepare("$existing_login");
    my $existing_count = $prep_existing->execute();
    
    if ($existing_count eq '0E0') {
      print "<p>SuperUser account does not exist yet!</p>" if $testing;

      my $insert_allowed = 0;
      my @errors;
   ##   if ($username !~ /(?=.*[a-z]).{5,}/) {
   ##     push(@errors, 'Username does not have proper formatting.');
   ##   }
      if ($password !~ /(?=.*[A-z])(?=.*[0-9]).{8,}/) {
        push(@errors, 'Password does not have proper formatting.');
      }
      my $start = "START TRANSACTION;";
      print $start if $testing;
      my $prep = $dbi_connection->prepare("$start");
      my $start_exec = $prep->execute();

      print "<br>LIST: $ncpdp<br>" if $testing;
	  $ncpdp =~ s/\s//g;
      my @ncpdps = split(',', $ncpdp);
      my $ncpdp_array_size = @ncpdps; 
	  
      my @ncpdp_quote;
      foreach my $ncpdp (@ncpdps) {
        push (@ncpdp_quote, $dbi_connection->quote($ncpdp));
        if ($ncpdp !~ /^(\s|)[0-9]{7}(\s|)$/) {
          push (@errors, "NCPDP $ncpdp is incorrectly formatted.");
        }
      }
      
      my $quoted_ncpdp = join(',', @ncpdp_quote);

      if ($USER == 66 || $USER == 2451) { ################# change to unless #########################
        print "Restricted access!" if $testing;
        print "Checking for appropriate allowances" if $testing;
        
        my $check = qq#
          SELECT FEIN
          FROM $db_office.pharmacy
          WHERE NCPDP IN ($quoted_ncpdp)
          GROUP BY FEIN;
        #;
       ## my $check_prep = $dbi_connection->prepare("$check");
       ## my $check_result = $check_prep->execute();
       my $check_result = 1;
        
        if ($check_result != 1) {
          push (@errors, "Multiple or zero pharmacy groups found. Aborting SuperUser creation.");
        } else {
          $insert_allowed = 1;
        }
      } else {
        $insert_allowed = 1;
      }
      print "NCPDPS $quoted_ncpdp<br>" if $testing;
      if ($insert_allowed) {
        my $pharmacy_ids = qq ~
        SELECT pharmacy_id
        FROM $db_office.pharmacy
        WHERE NCPDP IN ($quoted_ncpdp);
        ~;

        my $pharm_prep = $dbi_connection->prepare("$pharmacy_ids");
        my $exec = $pharm_prep->execute();

        $first_pharmacy_id = $pharm_prep->fetchrow_array();
       
	    my $super;
        if ($ncpdp_array_size > 1) {
		   $super = "SuperUser";
		} else {
		   $super = "User";
		}
		    
	    #my $super = $ncpdp =~ /[0-9]{7}(\s|),(\s|)[0-9]{7}/ ? 'SuperUser':'User';
		
        
        my $insert_superuser = qq~
        INSERT INTO $db_office.$tbl_weblogin (login, password, type, access,
          programs, comments, permission_level, display_in_menus, aggregated)
        VALUES ($username_quote, AES_ENCRYPT($password_quote, 'PAI20181217!'), '$super',
          '$first_pharmacy_id', '$programs', '', 'NONE', 'No', '$agg_binary');
        ~;
        my $super_prep = $dbi_connection->prepare($insert_superuser);
        $super_prep->execute();
        
        print $insert_superuser if $testing;
        
        my $login_id;
        my $login = qq~
        SELECT id
        FROM $db_office.$tbl_weblogin
        WHERE login = $username_quote;
        ~;
        print $login if $testing;
        my $login_prep = $dbi_connection->prepare("$login");
        my $login_execute = $login_prep->execute();

        if ($login_execute != 1) {
          push (@errors, 'Two logins match! Please contact IT to correct this.');
        } else {
          my ($login_id) = $login_prep->fetchrow_array();
          
          while (my $pharm_id = $pharm_prep->fetchrow_array()) {
            
            my $web_detail = qq~
              INSERT INTO $db_office.$tbl_webdtl  
              (login_id, pharmacy_id, program)
              VALUES('$login_id', '$pharm_id', '$programs');
            ~;
            print $web_detail if $testing;
            my $web_dprep = $dbi_connection->prepare("$web_detail");
            $web_dprep->execute();
          }
        } 
      }

      if (!@errors) {
        if ($warning_ncpdp) {
          print qq~
            <div class="warning-msg">
              <i class="fa fa-warning"></i>
              'Aggregate' checked, but only 1 NCPDP was added. Aggregate was removed before adding user.
            </div>~;
        }
        
        print qq~
          <div class="success-msg">
            <i class="fa fa-check"></i>
            New user successfully added!
          </div>~;
          my $commit = "COMMIT;";
          print $commit if $testing;
          my $prep_rollback = $dbi_connection->prepare("$commit");
          my $exec_rollback = $prep_rollback->execute();
      } else {
        my $error_msg = join(' ', @errors);
        print qq~
          <div class="error-msg">
            <i class="fa fa-times-circle"></i>
            $error_msg
          </div>~;
        
        my $rollback = "ROLLBACK;";
        print $rollback if $testing;
        my $prep_rollback = $dbi_connection->prepare("$rollback");
        my $exec_rollback = $prep_rollback->execute();
      }
      
    } else {
      print qq~
        <div class="error-msg">
          <i class="fa fa-times-circle"></i>
          SuperUser with that login account already exists!
        </div>~;
        
        my $rollback = "ROLLBACK;";
        print $rollback if $testing;
        my $prep_rollback = $dbi_connection->prepare("$rollback");
        my $exec_rollback = $prep_rollback->execute();
    }
  } else {
    print "<p>Please fill out all required information to continue</p>";
  }
}
#______________________________________________________________________________
