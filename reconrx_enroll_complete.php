<?php

$testing = false;
$testingEmailAddress = '';

#Required includes
require_once('./includes/mysql.php');
require_once('./includes/sendmail_mandrill.php');
require_once('./includes/FPDF/fpdf.php');
require_once('./includes/FPDI/fpdi.php');
require_once('./includes/FPDF/draw.php');
require_once('./includes/PHPWord.php');

require_once('./cgi-bin/SendEmails/vendor/autoload.php');
require_once('./cgi-bin/SendEmails/vendor/docusign/esign-client/autoload.php');

##include_once 'includes/ds_config_dev.php';
include_once 'includes/ds_config.php';
include_once 'includes/ds_base.php';
include_once 'includes/send_envelope.php';
include 'D:/WWW/vars.php';


### RECON GLOBALS TO BE USED FOR ALL DOCUMENTS ################################
$recon{'Rx_Name'}             = "ReconRx/Outcomes Operating, Inc.";
##$recon{'Rx_DBA'}              = "Outcomes Operating, Inc. dba ReconRx";
$recon{'Rx_DBA'}              = "Outcomes Operating,Inc(ReconRx)";
$recon{'Rx_ID'}               = "PHARM ASSESS";
$recon{'Rx_Password'}         = "PArbs1996";

$recon{'Rx_Signer'}          = "John Schaefer";
$recon{'Rx_Signer_Title'}    = "Chief Legal Officer";
$recon{'Rx_Signer_Email'}    = "JSchaefer@Outcomes.com";

$recon{'Rx_Contact'}          = "Jessie Kanatzar";
$recon{'Rx_Contact_Title'}    = "Program Manager";
$recon{'Rx_Contact_Email'}    = "RECON@Outcomes.com";
$recon{'Rx_Alt_Contact'}      = "Mark Olberding";
$recon{'Rx_Alt_Contact_Email'} = "RECON@Outcomes.com";
$recon{'Rx_Contact_Phone'}    = "(913) 897-4343";
$recon{'Rx_Contact_Phone_NB'} = "913 897-4343";
$recon{'Rx_Contact_Ext'}      = "ext. 117";
$recon{'Rx_Fax_Number'}       = "(888) 618-8535";
$recon{'Rx_Fax_Number_NB'}    = "888 618-8535";
$recon{'Rx_Fax_Number2'}      = "(913) 897-4344";
$recon{'Rx_Mailing_Address'}  = "1001 E. 101st Terrace, Suite 250";
$recon{'Rx_Pa_Address'}       = "1001 E. 101st Terr, Suite 250";
$recon{'Rx_Mailing_City'}     = "Kansas City";
$recon{'Rx_Mailing_State'}    = "MO";
$recon{'Rx_Mailing_Zip'}      = "64131";
$recon{'Rx_CS'}               = "Customer Service";
$recon{'Rx_CS_Email'}         = "RECON@Outcomes.com";
$recon{'Rx_IT'}               = "IT";
$recon{'Rx_IT_Email'}         = "PAIT@Outcomes.com";
$recon{'Rx_Prod_Email'}       = "TPP_Notice@Outcomes.com";
$recon{'Rx_Toll_Free_Phone'}  = "(888) 255-6526";
$recon{'Rx_Toll_Free_Fax'}    = "(888) 618-0262";
$recon{'Rx_Service_Center'}   = "2368";
$recon{'Rx_Submitter_ID'}     = "94960";
$recon{'Today'}               = date('m/d/Y');
#$recon{'Today'}               = '07/01/2021';

$date = explode('/', $recon{'Today'});

#$recon{'Month'}               = '7';
$recon{'Month'}               = $date[0];
#$recon{'Month_SP'}            = 'July';
$recon{'Month_SP'}            = date("F");
#$recon{'Day'}                 = '1';
$recon{'Day'}                 = $date[1];
$recon{'Year'}                = substr($date[2], 2, 2);
$recon{'Full_Year'}           = $date[2];
$recon{'Date'}                = date("F d, Y");
#$recon{'Date'}                = 'July 1, 2021';
$recon{'Quote_Exp'}           = date("F d, Y", strtotime("+90 day"));
$gmed_r835 = '';
$Outcomes = 0;

### ----------------------------------------------------------------------- ###
#
class PDF extends PDF_Draw {
}

$errorcheck = 0;
$instructions = "";
$instructions2 = "";
$rrx_page = basename($_SERVER['PHP_SELF']);
$rrx_status = "complete";
$today = date('m/d/Y');
$url = "$_SERVER[HTTP_HOST]";
$year = date('Y');

if ($testing == true) {
  #In a dev or testing environment, do not send emails
	$emailsend = false;
} else {
	$emailsend = true;
}

#Build Vendor_TPP Hash 
$vendor_tpp = array();
#$cp = array("AlignRx"=>"2000064", "Leadernet"=>"2000066", "GeriMed"=>"2000062", "Health Mart Atlas"=>"2000065", "Elevate"=>"2000067", "PPOK"=>"2000061", "Pharmacy First"=>"2000063");
$cp = array("AlignRx"=>"2000064", "Cardinal"=>"2000066", "GeriMed"=>"2000062", "Health Mart Atlas"=>"2000065", "Elevate"=>"2000067", "PPOK-Direct Chain Code"=>"2000061", "Pharmacy First-Direct Chain Code"=>"2000063");

if ($result = mysqli_query($mysqli, "SELECT vendor_id, tpp_id
                                       FROM officedb.vendor_tpp
                                   ORDER BY vendor_id, tpp_id")) {
  while ($row = mysqli_fetch_array($result)) {
    $key = $row{'vendor_id'} . "##" . $row{'tpp_id'};
    $vendor_tpp{$key} = "1";
  }
}
else {
  $error = "Problem querying your data.";
  echo "Problem querying your data. " . mysqli_error($mysqli);
}

#

#Set NCPDP/NPI for building agreement packet

#First, if regenerate POST variables are present, use them
if (isset($_POST["regenerate_ncpdp"]) && isset($_POST["regenerate_npi"])) {
	$returning_ncpdp = $_POST["regenerate_ncpdp"];
	$returning_npi = $_POST["regenerate_npi"];
	$emailsend = false; #Do not send pharmacy or staff an email if this is just to regenerate paperwork
	$admin_mode++; #Setting admin mode will serve up admin version of header
	
#Second, check cookies for a 'regular' enrollment coming from reconrx_enroll01.php
} else if (isset($_COOKIE["rrx_ncpdp"]) && isset($_COOKIE["rrx_npi"])) {
	$returning_ncpdp = $_COOKIE["rrx_ncpdp"];
	$returning_npi = $_COOKIE["rrx_npi"];
	
#Otherwise, kick back to enroll.php page (unless in testing mode)
} else {
  if (!$testing) {
	  header('Location: /enroll.php');
	  exit();
  }
##	$returning_ncpdp =  4436806;
##	$returning_npi = 1043225675;
}


###SET VALUES TO DB################################################
if ($stmt = $mysqli->prepare("
		UPDATE reconrxdb.enrollment SET
		rrx_status=? 
		WHERE rrx_ncpdp=? && rrx_npi=?
		;")) {
		$stmt->bind_param('sii', $rrx_status, $returning_ncpdp, $returning_npi);
		$stmt->execute();
		$stmt->close();
	}
	else {
		printf("Prepared Statement Error: %s\n", $mysqli->error);
		$errorcheck = 1;
}
###################################################################

###READ VALUES FROM DB#############################################
if ($result = mysqli_query($mysqli, "SELECT 
                                  rrx_pharmname AS Pharmacy_Name,
	                          rrx_ncpdp AS NCPDP,
			          rrx_legalname AS Legal_Name,
                                  rrx_npi AS NPI,
                                  rrx_main_address1 AS Address,
                                  rrx_main_address2 AS Address2,
                                  rrx_main_city AS City,
                                  rrx_main_state AS State,
                                  rrx_main_zip AS Zip,
                                  rrx_mailing_address1 AS Mailing_Address,
                                  rrx_mailing_address2 AS Mailing_Address2,
                                  rrx_mailing_city AS Mailing_City,
                                  rrx_mailing_state AS Mailing_State,
                                  rrx_mailing_zip AS Mailing_Zip,
                                  rrx_phone AS Business_Phone,
                                  rrx_fax AS Fax_Number,
                                  rrx_email AS Email_Address,
                                  rrx_fed_tax_id AS FEIN,
                                  rrx_fed_tax_class AS Fed_Tax_Classification,
                                  rrx_owner_contact_name AS Owner_Contact_Name,
                                  rrx_owner_contact_email AS Owner_Contact_Email,
                                  rrx_owner_contact_phone AS Owner_Contact_Phone,
                                  rrx_owner_contact_fax AS Owner_Contact_Fax,
                                  rrx_main_contact_name AS Primary_Contact_Name,
                                  rrx_main_contact_title AS Primary_Contact_Title,
                                  rrx_main_contact_email AS Primary_Contact_Email,
                                  rrx_main_contact_phone AS Primary_Contact_Phone,
                                  rrx_main_contact_fax AS Primary_Contact_Fax,
                                  rrx_auth_contact_name AS Authorized_Contact_Name,
                                  rrx_auth_contact_title AS Authorized_Contact_Title,
                                  rrx_auth_contact_email AS Authorized_Contact_Email,
                                  rrx_auth_contact_phone AS Authorized_Contact_Phone,
                                  rrx_auth_contact_fax AS Authorized_Contact_Fax,
                                  rrx_switch AS Primary_Switch,
                                  rrx_swvendor AS Software_Vendor,
				  rrx_source,
				  rrx_psao AS PSAO,
                                  rrx_service_level AS Service_Level,
				  rrx_medicaid AS Medicaid_Primary_Num,
				  id,
				  rrx_affiliate AS Affiliate,
                                  rrx_promo_code AS PromoCode
                                FROM reconrxdb.enrollment 
			       WHERE rrx_ncpdp = $returning_ncpdp && rrx_npi = $returning_npi
                            ORDER BY COO DESC")) {
    $pull = mysqli_fetch_assoc($result);

    $brackets = array(')','(');
    $pull{'Business_Phone_NB'} = str_replace($brackets, '' , $pull{'Business_Phone'});
    $pull{'Fax_Number_NB'} = str_replace($brackets, '' , $pull{'Fax_Number'});
    $pull{'Primary_Contact_Phone_NB'} = str_replace($brackets, '' , $pull{'Primary_Contact_Phone'});
    $pull{'Primary_Contact_Fax_NB'} = str_replace($brackets, '' , $pull{'Primary_Contact_Fax'});

    mysqli_free_result($result);
}
else {
    printf("Prepared Statement Error: %s\n", $mysqli->error);
}

if ($pull{'PromoCode'} == '') {
  $pull{'PromoCode'} = 'Standard';
}

$code = $pull{'PromoCode'};

if ($pull{'Software_Vendor'} == 'ComputerRx' || $pull{'Software_Vendor'} == 'Rx30') {
  $Outcomes = 1;
}

if ($pull{'PSAO'} == 'AlignRx') {
  if ($pull{'Service_Level'} == 'B') {
    $code = 'AlignRxB';
  }
}

if ($pull{'Affiliate'} == 'GeriMed') {
    $code = 'GeriMed';
}


if ($result = mysqli_query($mysqli, "SELECT Price, OutcomesPrice, Affiliate
                                       FROM officedb.promo_mst 
   			              WHERE Promo = '$code' 
                                         && Active
                                    ")) {
    $promodata = mysqli_fetch_assoc($result);
}

$amount  = $promodata{'Price'};
$affilte = $promodata{'Affiliate'};

if ($amount == '') {

  if ($result = mysqli_query($mysqli, "SELECT Price, OutcomesPrice, Affiliate
                                         FROM officedb.promo_mst 
     			              WHERE Promo = 'Standard' 
                                           && Active
                                      ")) {
      $promodata = mysqli_fetch_assoc($result);
  }

  $amount  = $promodata{'Price'};
  $affilte = $promodata{'Affiliate'};

}


if($Outcomes) {
  $amount = $promodata{'OutcomesPrice'};
}
if($affilte && $pull{'Affiliate'} == '') {
  if ($stmt = $mysqli->prepare("
    	  	  UPDATE reconrxdb.enrollment SET
  		  rrx_affiliate=? 
		  WHERE rrx_ncpdp=? && rrx_npi=?
		  ;")) {
		  $stmt->bind_param('sii', $affilte, $returning_ncpdp, $returning_npi);
		  $stmt->execute();
		  $stmt->close();
  }
  else {
		printf("Prepared Statement Error: %s\n", $mysqli->error);
		$errorcheck = 1;
  }
}
###################################################################

##################################################################

####Combine Pharmacy and ReconRx Data for output##################
$input = array_merge($pull, $recon);

###################################################################

###START PDF BUILDING PROCESS######################################
$folder = 'enrollments/'.$input{'NCPDP'};
if (!file_exists($folder)) {
	mkdir($folder,0777);
}

// initiate FPDI
$pdf = new PDF();
$pageno = 1; #This must be incremented (++) on each page added.
$pagenox = 198; #location on the page to display page number (x)
$pagenoy = 270; #location on the page to display page number (y)

#//Set global PDF values
$pdf->SetCompression(false);
$pdf->SetAutoPageBreak(false);
$pdf->SetFont('Helvetica');
$pdf->SetFontSize(10);
$pdf->SetTextColor(0, 0, 0);

# Add ReconRx Agreement -----------------------------------------------------------------
$packet_id = 87;

$input{'Rx_Amount'} = $amount;

$db = 'reconrxdb';

$form_id = array();
$SignHere = [];
$DateSigned = [];
$Text = [];
$Zip = [];
$Number = [];
$Checkbox = [];
$RadioGroup = [];
$Radio = [];

$Recon_SignHere = [];
$Recon_DateSigned = [];

if ($result = mysqli_query($mysqli, "SELECT c.id AS frm_id, a.name AS form_name, c.location, c.pages, c.instructions
                                       FROM $db.835auth_frms a, $db.835auth_frms_dtl b, $db.form_mst c
                                      WHERE a.id = b.auth_mst_id
                                        AND b.frm_mst_id = c.id
                                        AND a.id = $packet_id
                                   ORDER BY b.seq;")) {
  while ($form = mysqli_fetch_array($result)) {
    $form{'location'} = substr($form{'location'}, 3);

    #### Loop through pages of Form adding $input values
    for ($pg = 1; $pg <= $form{'pages'}; $pg++) {
      $pdf->AddPage();
      if ($pg == 1) {       
        $pdf->setSourceFile($form{'location'});
      }
      $page = $pdf->importPage($pg);
      $pdf->useTemplate($page, null, null, 0, 0, true);

      add_data($mysqli, $pdf, $form{'frm_id'}, $pg, $input);

      $pdf->SetXY($pagenox, $pagenoy); 
      $pdf->Write(0, "$pageno"); 
      $pageno++; 
    }

    array_push($form_id, $form{'frm_id'});    
  }

  
  if ($pull{'Affiliate'} == 'GeriMed') {
      $gmed_r835 = 'Yes';
  }
  ## Addendum Section
  $addend_loc = '';

  if ( $pull{'PSAO'} == 'Pharmacy First-Direct Chain Code' ) {
    $addend_loc = 'docs/setup_forms/Prime_Therapeutics_Pharmacy_First.pdf';
    $frm_id = '58';	   	  
    array_push($form_id, $frm_id);
  }
  elseif ( $pull{'PSAO'} == 'PPOK-Direct Chain Code' ) {
    $addend_loc = 'docs/setup_forms/Prime_Therapeutics_Electronic_Remit_Opt-Out_PBA_PPOK.pdf';
    $frm_id = '59';
    array_push($form_id, $frm_id);
  }
  
  if ( $addend_loc != '') {
    $pdf->AddPage();
    $pdf->setSourceFile($addend_loc);
    $page = $pdf->importPage(1);
    $pdf->useTemplate($page, null, null, 0, 0, true);

    add_data($mysqli, $pdf, $frm_id, 1, $input);

    $pdf->SetXY($pagenox, $pagenoy); 
    $pdf->Write(0, "$pageno"); 
    $pageno++; 
  }

  if ( $pull{'PSAO'} == 'Pharmacy First-Direct Chain Code' ) {
    $addend_loc = 'docs/setup_forms/PharmacyFirst_835_Split_Enrollment.pdf';
    $frm_id = '106';	   	  
    array_push($form_id, $frm_id);

    $pdf->AddPage();
    $pdf->setSourceFile($addend_loc);
    $page = $pdf->importPage(1);
    $pdf->useTemplate($page, null, null, 0, 0, true);

    add_data($mysqli, $pdf, $frm_id, 1, $input);

    $pdf->SetXY($pagenox, $pagenoy); 
    $pdf->Write(0, "$pageno"); 
    $pageno++; 
  }

  ###

  ## Software Vendors Section
  if ($result3 = mysqli_query($mysqli, "SELECT id AS frm_id, form_name, location, pages, instructions
                                          FROM $db.form_mst
 				         WHERE form_type = 'SWT'
                                           AND active = 1
                                      ORDER BY id;")) {
    while ($swv = mysqli_fetch_array($result3)) {
      $use = 1;    
      $swv['location'] = substr($swv['location'], 3);

      if ( preg_match("/New Tech|RedSail/", $swv{'form_name'}) ) {
        if ( (preg_match("/New Tech/", $swv{'form_name'}) && preg_match("/Pioneer/", $pull{'Software_Vendor'})) || (preg_match("/RedSail/", $swv['form_name']) && $pull['Software_Vendor'] == 'RedSail') ) {
          $use = 1;
        }
        else {
          $use = 0;	
        }
      }

      if ( $use == 1 ) {
        #### Loop through pages of Form adding $input values
        for ($pg = 1; $pg <= $swv{'pages'}; $pg++) {
          $pdf->AddPage();
          if ($pg == 1) {       
            $pdf->setSourceFile($swv{'location'});
          }
          $page = $pdf->importPage($pg);
          $pdf->useTemplate($page, null, null, 0, 0, true);

          add_data($mysqli, $pdf, $swv{'frm_id'}, $pg, $input);

          $pdf->SetXY($pagenox, $pagenoy); 
          $pdf->Write(0, "$pageno"); 
          $pageno++; 
        }

        array_push($form_id, $swv{'frm_id'});
      }
    }
  }
  else {
    $error = "Problem querying your data.";
  }

  ###
  if ($result = mysqli_query($mysqli, "SELECT Receiving835s 
                                         FROM reconrxdb.gerimed_membership
                                         WHERE NCPDP = " . $input{'NCPDP'})) {
      $row = mysqli_fetch_assoc($result);
      if ($result->num_rows > 1) {
        $gmed_r835 = $row{'Receiving835s'};
      }
      else {
        $gmed_r835 = 'Yes';
      }
  }
  else {
      $gmed_r835 = 'Yes';
   ## $error = "Problem querying your data.";
   ## echo "Problem querying your data. " . mysqli_error($mysqli);
  }

  ## 835 Section
  if ($result2 = mysqli_query($mysqli, "SELECT id AS frm_id, tpp_id, form_name, location, pages, instructions
                                         FROM $db.form_mst
					WHERE form_type IN ('835', 'EFT')
					  AND tpp_id IS NOT NULL
					  AND active = 1
                                          AND packet = 1
                                     ORDER BY id;")) {
    while ($auth = mysqli_fetch_array($result2)) {
      $use = 1;    
      $auth{'location'} = substr($auth{'location'}, 3);
      $inst = explode('|', $auth{'instructions'});

      if ($pull{'rrx_source'} == 'qcp' && $auth{'tpp_id'} == '700009') {
        $use = 0;	
      }

      if ( array_key_exists($pull['PSAO'], $cp) ) {
        $vendor_id = $cp{$pull{'PSAO'}};
        $key = $vendor_id . "##" . $auth['tpp_id'];

        if ( array_key_exists($key, $vendor_tpp) ) {
	  $use = 0;	
	}
      }
      elseif ( $auth{'tpp_id'} == '700470' || $auth{'tpp_id'} == '700641' || $auth{'tpp_id'} == '700447' ) {
        $use = 0;
      }

      $state = $input['State'];

      if ( preg_match("/Medicaid/", $auth['form_name']) ) {
        if ( preg_match("/$state/", $auth['form_name']) ) {
          $use = 1;
        }
        else {
          $use = 0;	
        }
      }

     if ( preg_match("/RelayHealth_835/", $auth['form_name'])) {
        if (preg_match("/PPOK|Relay Health/", $pull{'Primary_Switch'})) {
          $use = 1;
        }
        else {
          $use = 0;	
        }
      }


      if ($pull{'Affiliate'} == 'GeriMed' && $gmed_r835 == 'No') {
        $use = 1;
      }

      if ( $use == 1 ) {
        #### Loop through pages of Form adding $input values
        for ($pg = 1; $pg <= $auth{'pages'}; $pg++) {
          $pdf->AddPage();
          if ($pg == 1) {       
            $pdf->setSourceFile($auth['location']);
          }
          $page = $pdf->importPage($pg);
          $pdf->useTemplate($page, null, null, 0, 0, true);

          add_data($mysqli, $pdf, $auth['frm_id'], $pg, $input);

          $pdf->SetXY($pagenox, $pagenoy); 
          $pdf->Write(0, "$pageno"); 
          $pageno++; 
        }

	array_push($form_id, $auth{'frm_id'});
      }
    }
  }
  else {
    $error = "Problem querying your data.";
    echo "Problem querying your data. " . mysqli_error($mysqli);
  }
}
else {
  $error = "Problem querying your data.";
  echo "Problem querying your data. " . mysqli_error($mysqli);
}

$packet = "enrollments/" . $input{'NCPDP'} . "/" . $input{'NCPDP'} . "_ReconRx_Agreement_Packet.pdf";

$pdf->Output($packet);

#### Save form order in Packet 
#if (!isset($_POST["regenerate_ncpdp"]) && !isset($_POST["regenerate_npi"])) {
	foreach ($form_id as $frm) {
		#echo "Form Used: $id\n";
		if ($stmt = $mysqli->prepare("
			INSERT INTO reconrxdb.enrollment_packet (enrollment_id, frm_mst_id)
        	        VALUES (?, ?)
			;")) {
			$stmt->bind_param('ii', $input['id'], $frm);
			$stmt->execute();
			$stmt->close();
		}
		else {
			printf("Prepared Statement Error: %s\n", $mysqli->error);
			$errorcheck = 1;
		}
	}
#}

$config = new DocuSign\eSign\Configuration();
$apiClient = new DocuSign\eSign\Client\ApiClient($config);
?>

<!--Header and Navigation-------------------------------------------->
<!doctype html> 
<html lang="en">
<?php include 'includes/header_nav.php'; ?>
<div id="wrapper"><!-- wrapper -->
<div id="content_container_front">
<div id="mainbody_front">
<!------------------------------------------------------------------->

  <h1>DocuSign Contracts</h1>

<?php

echo "<p>The online portion of your enrollment is now complete.</p>";

try {
#  print("\nSending an envelope...\n");
  $sendHandler = new SendEnvelope($apiClient);
  $result = $sendHandler->send($packet, $input['Authorized_Contact_Name'], $input['Authorized_Contact_Email']);
  
  echo "<div class=\"review_page\"><p><strong>Important</strong>: Sign and Submit your completed Agreement Packet through DocuSign.</p></div>\n";

  echo '<p style="margin-top: 40px;">Thank you for completing our ReconRx online enrollment form! An email containing our ReconRx Agreement has been sent to the email you provided via DocuSign. Please complete the ReconRx Agreement at your earliest convenience. Once completed, your ReconRx Account Manager will contact you. We look forward to providing reconciliation services for your pharmacy!</p>';

  printf("<br>Envelope status: %s. Envelope ID: %s<br>", $result->getStatus(), $result->getEnvelopeId());
} catch (Exception $e) {
  echo "<p style=\"color: #F00;\"><strong>There was a problem generating your agreement packet, please call or email ReconRx for assistance.</strong></p>";

  print ("\n\nException!\n");
  print ($e->getMessage());

  if ($e instanceof DocuSign\eSign\ApiException) {
    print ("\nAPI error information: \n");
    print ($e->getResponseObject());
  }
}

?>

</div><!-- end mainbody_front -->

<!-- Sidebar -------------------------------------------------------->
<div id="sidebarWrapper">
<div id="sidebar">
<h2>Contact</h2>
<p>Phone: <?php echo $input{'Rx_Fax_Number'}; ?></p>
<p>Email: 
Recon@Outcomes.com
</p>
<h2>Need some help?</h2>
<p>If at any time you need assistance completing this enrollment, please call or send us an email at the contacts listed above.</p>

</div> <!-- end sidebarWrapper -->
</div> <!-- end sidebar -->
<!------------------------------------------------------------------->

<!--Footer----------------------------------------------------------->
</div><!-- end content_container_front -->
<?php include 'includes/footer.php'; ?>
<!------------------------------------------------------------------->

</div>

</body>
</html>

<?php 
##if (!file_exists('\\\\'. $FLSERVER .'\\DataShare\\ReconRx\\Documents\\Enrollment\\Online Enrollments\\'.$input{'NCPDP'}.'')) {
##    mkdir('\\\\' . $FLSERVER . '\\DataShare\\ReconRx\\Documents\\Enrollment\\Online Enrollments\\'.$input{'NCPDP'}, 0777, true);
##}

$file = 'enrollments/'.$input{'NCPDP'}.'/'.$input{'NCPDP'}.'_ReconRx_Agreement_Packet.pdf';
$newfile = '\\\\' . $FLSERVER . '\\DataShare\\ReconRx\\Documents\\Enrollment\\Online Enrollments\\'.$input{'NCPDP'}.'\\'.$input{'NCPDP'}.'_ReconRx_Agreement_Packet.pdf';
##if (!copy($file, "$newfile")) {
##	echo "file:".$file."<br />";
##	echo "newfile:".$newfile."<br />";
 ##   echo "1. failed to copy $file...<hr>\n";
##}

$source_notification = '';
if ($input{'rrx_source'} != '') {
	$source_notification = "(NOTE: $input{'rrx_source'} store)";
}

#if ($pull{'PSAO'} == 'AlignRx') {
#  $to = 'RECON@tdsclinical.com';
#  $subject = 'ReconRx Online Enrollment Approved by AlignRx!';
#  $updateBody      = $input{'Pharmacy_Name'} . " enrollment has been approved by AlignRx!";
#}
#else {
  $to = 'RECON@outcomes.com';
##  $to = 'PAIT@outcomes.com';
  $subject = 'ReconRx Online Enrollment Completed!';
  $updateBody      = $input{'Pharmacy_Name'} . "$source_notification has completed their online enrollment!<br/>Contact Name: " . $input{'Primary_Contact_Name'} . "<br/>NCPDP: " . $input{'NCPDP'} . "<br/>Call: " . $input{'Business_Phone'} . "<br/>Email: " . $input{'Email_Address'} . "<br/><br/>Switch: " . $input{'Primary_Switch'} . "<br/>Software: " . $input{'Software_Vendor'};
#}

if ($emailsend == "true") {
  system("cmd /c D:\\RedeemRx\\Programs\\SendEmails\\send_email.bat \"$to\" \"$subject\" \"$updateBody\"");
}

##if (file_exists('enrollments/'.$input{'NCPDP'}.'/' . $input{'NCPDP'} . '_ReconRx_Agreement_Packet.pdf')) {
##unlink('enrollments/'.$input{'NCPDP'}.'/' . $input{'NCPDP'} . '_ReconRx_Agreement_Packet.pdf');
##}

function add_data($mysqli, $pdf, $form_id, $pg, $input) {
  $dbase = $GLOBALS['db'];
#  echo "INTO add_data<br>";
  if ($result = mysqli_query($mysqli,"SELECT * FROM $dbase.form_dtl WHERE form_mst_id = $form_id AND form_page = $pg AND bank_info = 0;")) {
    while ($dtl = mysqli_fetch_array($result)) {
      $val = $dtl{'value'};
      $docusign = $dtl{'docusign'};
      $tab_type = $dtl{'ds_type'};

      if ( $docusign ) {
        $sender_id = substr($val,0,1);
        $val = substr($val, 2);
        $x = intval($dtl{'x_cord'});
	$y = intval($dtl{'y_cord'});

        if ( $sender_id == 'R' ) {
          if ( $tab_type == 'SignHere' ) {
            array_push($GLOBALS['SignHere'], new DocuSign\eSign\Model\SignHere([ # DocuSign SignHere field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' => $x, 'y_position' => $y
                      ]));
          }
  	  elseif ( $tab_type == 'DateSigned' ) {
            array_push($GLOBALS['DateSigned'], new DocuSign\eSign\Model\DateSigned([ # DocuSign SignHere field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' => $x, 'y_position' => $y
                      ]));
          }
  	  elseif ( $tab_type == 'Text' ) {
            array_push($GLOBALS['Text'], new DocuSign\eSign\Model\Text([ # DocuSign Text field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' =>$x, 'y_position' => $y
                      ]));
	  }
  	  elseif ( $tab_type == 'TextO' ) {
            array_push($GLOBALS['Text'], new DocuSign\eSign\Model\Text([ # DocuSign Text field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' =>$x, 'y_position' => $y, 'required' => 'false'
                      ]));
	  }	  
          elseif ( $tab_type == 'Number' ) {
            array_push($GLOBALS['Number'], new DocuSign\eSign\Model\Number([ # DocuSign Text field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' => $x, 'y_position' => $y
                      ]));
	  }
          elseif ( $tab_type == 'NumberO' ) {
            array_push($GLOBALS['Number'], new DocuSign\eSign\Model\Number([ # DocuSign Text field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' => $x, 'y_position' => $y, 'required' => 'false'
                      ]));
	  }	  
	  elseif ( $tab_type == 'Zip' ) {
            array_push($GLOBALS['Zip'], new DocuSign\eSign\Model\Zip([ # DocuSign Zip field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
	               'tab_label' => "$val", 'x_position' => $x, 'y_position' => $y
                      ]));
	  }
	  elseif ( $tab_type == 'Checkbox' ) {
            array_push($GLOBALS['Checkbox'], new DocuSign\eSign\Model\Checkbox([ # DocuSign Checkbox field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' =>$x, 'y_position' => $y
                      ]));
	  }
	  elseif ( $tab_type == 'Radio' ) {
            array_push($GLOBALS['Radio'], new DocuSign\eSign\Model\Radio([ # DocuSign Radio field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' =>$x, 'y_position' => $y
                      ]));
	  }	  
	}
	else {
          if ( $tab_type == 'SignHere' ) {
            array_push($GLOBALS['Recon_SignHere'], new DocuSign\eSign\Model\SignHere([ # DocuSign SignHere field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' => $x, 'y_position' => $y
                      ]));
          }
  	  elseif ( $tab_type == 'DateSigned' ) {
            array_push($GLOBALS['Recon_DateSigned'], new DocuSign\eSign\Model\DateSigned([ # DocuSign SignHere field/tab
                       'document_id' => '1', 'page_number' => $GLOBALS['pageno'], 'recipient_id' => '1',
                       'tab_label' => "$val", 'x_position' => $x, 'y_position' => $y
                      ]));
          }
	}
      }
      else {
        if (preg_match_all("/[{}]/", $val)) {
          $pcs = preg_split('/\s+/', $val);
          foreach ($pcs as $pc) {
            $key = preg_replace("/[{},]/", "", $pc);
	    $pc = preg_replace("/,/", "", $pc);
            if (array_key_exists($key, $input)) {
              $val = preg_replace("/$pc/", $input{$key}, $val);
  	    }
          }
        }
        else {
          if (array_key_exists($dtl{'value'}, $input)) {
            $val = $input{$dtl{'value'}};
	  }
	  else {
            $val = $dtl{'value'};
          }
        }
        $pdf->SetXY($dtl{'x_cord'}, $dtl{'y_cord'});
        $pdf->Write(0, $val);
      }
    }

    if ( count($GLOBALS['Radio']) > 0 ) {
            array_push($GLOBALS['RadioGroup'], new DocuSign\eSign\Model\RadioGroup([ # DocuSign RadioGroup field/tab
                       'document_id' => '1', 'groupName' => 'RadioGroup1', 'recipient_id' => '1',
                       'radios' => $GLOBALS['Radio']
                      ]));
    }    
  }
  else {
    $error = "Problem querying your data.";
    echo "Problem querying your data. -" . mysqli_error($mysqli);
  }
}  

$mysqli->close();

?>
